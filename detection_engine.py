import os
from datetime import datetime, timedelta
from collections import defaultdict
from itertools import combinations
import math

import pandas as pd
from neo4j import GraphDatabase


class Neo4jGraphView:
    """Lightweight graph-like adapter so existing dashboard/backend code stays unchanged."""

    def __init__(self, driver):
        self.driver = driver

    def neighbors(self, node_id):
        query = """
        MATCH (n:Entity {id: $node_id})-[:LINKS]-(m:Entity)
        RETURN DISTINCT m.id AS id
        """
        with self.driver.session() as session:
            return [r["id"] for r in session.run(query, node_id=node_id)]

    def degree(self, node_id):
        query = """
        MATCH (n:Entity {id: $node_id})-[:LINKS]-(m:Entity)
        RETURN count(DISTINCT m) AS degree
        """
        with self.driver.session() as session:
            rec = session.run(query, node_id=node_id).single()
            return int(rec["degree"]) if rec else 0

    def __contains__(self, node_id):
        query = "MATCH (n:Entity {id: $node_id}) RETURN count(n) > 0 AS present"
        with self.driver.session() as session:
            rec = session.run(query, node_id=node_id).single()
            return bool(rec["present"]) if rec else False

    def number_of_nodes(self):
        query = "MATCH (n:Entity) RETURN count(n) AS c"
        with self.driver.session() as session:
            rec = session.run(query).single()
            return int(rec["c"]) if rec else 0

    def number_of_edges(self):
        query = "MATCH ()-[r:LINKS]-() RETURN count(r) AS c"
        with self.driver.session() as session:
            rec = session.run(query).single()
            return int(rec["c"]) if rec else 0


class CyberFinDetector:
    def __init__(self, cyber_df, txn_df):
        self.cyber_df = cyber_df.copy()
        self.txn_df = txn_df.copy()
        self.cyber_df["timestamp"] = pd.to_datetime(self.cyber_df["timestamp"])
        self.txn_df["timestamp"] = pd.to_datetime(self.txn_df["timestamp"])

        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")

        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.graph = Neo4jGraphView(self.driver)
        self.risk_scores = {}

    def _run(self, query, **params):
        with self.driver.session(database=self.database) as session:
            return list(session.run(query, **params))

    def _prepare_constraints(self):
        self._run(
            "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS "
            "FOR (e:Entity) REQUIRE e.id IS UNIQUE"
        )

    def build_graph(self):
        """Build Neo4j graph connecting accounts, devices, IPs, and beneficiaries."""
        self._prepare_constraints()

        # Rebuild graph from source data each run to match existing behavior.
        self._run("MATCH (n:Entity) DETACH DELETE n")

        cyber_rows = [
            {
                "account_id": row["account_id"],
                "device_id": f"DEV_{row['device']}",
                "ip_id": f"IP_{row['ip']}",
                "ts": row["timestamp"].isoformat(),
            }
            for _, row in self.cyber_df.iterrows()
        ]
        if cyber_rows:
            self._run(
                """
                UNWIND $rows AS row
                MERGE (a:Entity:Account {id: row.account_id})
                MERGE (d:Entity:Device {id: row.device_id})
                MERGE (i:Entity:IP {id: row.ip_id})
                MERGE (a)-[r1:LINKS {type: 'device'}]->(d)
                ON CREATE SET r1.last_seen = row.ts
                ON MATCH SET r1.last_seen = row.ts
                MERGE (a)-[r2:LINKS {type: 'ip'}]->(i)
                ON CREATE SET r2.last_seen = row.ts
                ON MATCH SET r2.last_seen = row.ts
                """,
                rows=cyber_rows,
            )

        txn_rows = [
            {
                "account_id": row["account_id"],
                "beneficiary": row["beneficiary"],
                "amount": float(row["amount"]),
                "ts": row["timestamp"].isoformat(),
            }
            for _, row in self.txn_df.iterrows()
        ]
        if txn_rows:
            self._run(
                """
                UNWIND $rows AS row
                MERGE (a:Entity:Account {id: row.account_id})
                MERGE (b:Entity:Beneficiary {id: row.beneficiary})
                MERGE (a)-[r:LINKS {type: 'transaction'}]->(b)
                ON CREATE SET r.last_amount = row.amount, r.last_ts = row.ts, r.txn_count = 1
                ON MATCH SET r.last_amount = row.amount, r.last_ts = row.ts, r.txn_count = coalesce(r.txn_count, 0) + 1
                """,
                rows=txn_rows,
            )

        print(f"✅ Graph built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")

    def detect_cyber_anomalies(self, account_id, time_window_minutes=60):
        """Detect suspicious cyber activity patterns."""
        recent_time = datetime.now() - timedelta(minutes=time_window_minutes)
        account_events = self.cyber_df[
            (self.cyber_df["account_id"] == account_id)
            & (self.cyber_df["timestamp"] >= recent_time)
        ]

        flags = []
        if len(account_events[account_events["event_type"] == "malware_signal"]) > 0:
            flags.append("malware_detected")
        if len(account_events[account_events["event_type"] == "new_device"]) > 0:
            flags.append("new_device")
        if len(account_events[account_events["event_type"] == "foreign_ip"]) > 0:
            flags.append("foreign_ip")
        if len(account_events[account_events["event_type"] == "password_reset"]) > 0:
            flags.append("password_reset")
        if len(account_events[account_events["event_type"] == "login_fail"]) >= 3:
            flags.append("multiple_login_failures")

        return flags

    def detect_financial_velocity(self, account_id, time_window_minutes=120):
        """Detect rapid/high-value transactions."""
        recent_time = datetime.now() - timedelta(minutes=time_window_minutes)
        account_txns = self.txn_df[
            (self.txn_df["account_id"] == account_id)
            & (self.txn_df["timestamp"] >= recent_time)
        ]

        flags = []
        if len(account_txns) >= 3:
            flags.append("rapid_transactions")
        if (account_txns["amount"] > 45000).any():
            flags.append("near_threshold_amount")
        if account_txns["amount"].sum() > 100000:
            flags.append("high_total_volume")

        return flags

    def detect_mule_rings(self):
        """Detect mule rings using weighted account-account communities (no NetworkX)."""
        txn_records = self._run(
            """
            MATCH (a:Entity:Account)-[:LINKS {type:'transaction'}]->(b:Entity:Beneficiary)
            RETURN a.id AS account_id, b.id AS beneficiary_id
            """
        )

        account_to_bens = defaultdict(set)
        ben_to_accounts = defaultdict(set)
        for r in txn_records:
            acc = r["account_id"]
            ben = r["beneficiary_id"]
            account_to_bens[acc].add(ben)
            ben_to_accounts[ben].add(acc)

        # Additional cyber relationship signals from source data.
        account_to_devices = defaultdict(set)
        account_to_ips = defaultdict(set)
        for _, row in self.cyber_df.iterrows():
            acc = row["account_id"]
            account_to_devices[acc].add(f"DEV_{row['device']}")
            account_to_ips[acc].add(f"IP_{row['ip']}")

        device_to_accounts = defaultdict(set)
        for acc, devices in account_to_devices.items():
            for dev in devices:
                device_to_accounts[dev].add(acc)

        ip_to_accounts = defaultdict(set)
        for acc, ips in account_to_ips.items():
            for ip in ips:
                ip_to_accounts[ip].add(acc)

        # Weighted similarity between account pairs.
        # beneficiary co-usage is strongest (2 points), device/ip co-usage moderate (1 each).
        pair_weight = defaultdict(int)

        for accounts in ben_to_accounts.values():
            if len(accounts) < 2:
                continue
            for a, b in combinations(sorted(accounts), 2):
                pair_weight[(a, b)] += 2

        for accounts in device_to_accounts.values():
            if len(accounts) < 2:
                continue
            for a, b in combinations(sorted(accounts), 2):
                pair_weight[(a, b)] += 1

        for accounts in ip_to_accounts.values():
            if len(accounts) < 2:
                continue
            for a, b in combinations(sorted(accounts), 2):
                pair_weight[(a, b)] += 1

        # Build weighted account adjacency and adaptively prune weak links so
        # one giant connected component does not swallow all suspicious groups.
        account_adj_w = defaultdict(dict)
        all_accounts = set(account_to_bens.keys()) | set(account_to_devices.keys()) | set(account_to_ips.keys())
        for (a, b), w in pair_weight.items():
            account_adj_w[a][b] = w
            account_adj_w[b][a] = w

        def build_components(threshold):
            account_adj = defaultdict(set)
            for a, nbrs in account_adj_w.items():
                for b, w in nbrs.items():
                    if w >= threshold:
                        account_adj[a].add(b)
            visited = set()
            comps = []
            for acc in sorted(all_accounts):
                if acc in visited or acc not in account_adj:
                    continue
                stack = [acc]
                comp = set()
                while stack:
                    cur = stack.pop()
                    if cur in visited:
                        continue
                    visited.add(cur)
                    comp.add(cur)
                    for nbr in account_adj[cur]:
                        if nbr not in visited:
                            stack.append(nbr)
                if len(comp) >= 3:
                    comps.append(sorted(comp))
            return comps

        # Try stricter thresholds first to produce multiple rings.
        unique_weights = sorted(set(pair_weight.values()))
        candidate_thresholds = sorted(unique_weights, reverse=True)
        if 2 not in candidate_thresholds:
            candidate_thresholds.append(2)
        candidate_thresholds = sorted(set(candidate_thresholds), reverse=True)

        best_components = []
        best_score = (-1, -1)  # (num_components, covered_accounts)
        for threshold in candidate_thresholds:
            comps = build_components(threshold)
            covered = sum(len(c) for c in comps)
            score = (len(comps), covered)
            if score > best_score:
                best_components = comps
                best_score = score
            if len(comps) >= 2:
                break

        components = best_components

        # If still one giant component, apply weighted label propagation inside the component.
        if len(components) <= 1 and components:
            comp_set = set(components[0])
            labels = {acc: acc for acc in comp_set}

            for _ in range(30):
                changed = False
                order = sorted(comp_set, key=lambda a: len(account_adj_w.get(a, {})), reverse=True)
                for node in order:
                    label_scores = defaultdict(float)
                    for nbr, w in account_adj_w.get(node, {}).items():
                        if nbr in comp_set:
                            label_scores[labels[nbr]] += float(w)
                    if not label_scores:
                        continue
                    best_label = sorted(label_scores.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
                    if labels[node] != best_label:
                        labels[node] = best_label
                        changed = True
                if not changed:
                    break

            lp_groups = defaultdict(list)
            for acc, label in labels.items():
                lp_groups[label].append(acc)
            lp_components = [sorted(v) for v in lp_groups.values() if len(v) >= 3]
            if len(lp_components) >= 2:
                components = lp_components

        # If still one giant component, split by rarest-shared relation anchor (beneficiary/device/ip).
        if len(components) <= 1 and components:
            ben_freq = {ben: len(accs) for ben, accs in ben_to_accounts.items()}
            dev_freq = {dev: len(accs) for dev, accs in device_to_accounts.items()}
            ip_freq = {ip: len(accs) for ip, accs in ip_to_accounts.items()}
            comp_accounts = components[0]
            comp_size = len(comp_accounts)
            bucket = defaultdict(list)
            comp_set = set(comp_accounts)
            for acc in comp_accounts:
                candidates = []
                for ben in account_to_bens.get(acc, []):
                    freq = ben_freq.get(ben, 0)
                    if 3 <= freq < comp_size:
                        candidates.append(("BEN_" + ben, freq))
                for dev in account_to_devices.get(acc, []):
                    freq = dev_freq.get(dev, 0)
                    if 3 <= freq < comp_size:
                        candidates.append(("DEV_" + dev, freq))
                for ip in account_to_ips.get(acc, []):
                    freq = ip_freq.get(ip, 0)
                    if 3 <= freq < comp_size:
                        candidates.append(("IP_" + ip, freq))
                if not candidates:
                    continue
                anchor = sorted(candidates, key=lambda x: (x[1], x[0]))[0][0]
                bucket[anchor].append(acc)
            split_components = [sorted(v) for v in bucket.values() if len(v) >= 3]
            if len(split_components) >= 2:
                components = split_components

        # Final deterministic fallback for extremely dense single-cluster datasets.
        if len(components) <= 1 and components and len(components[0]) >= 60:
            comp_accounts = sorted(components[0])
            chunk_size = max(25, min(120, int(math.sqrt(len(comp_accounts)) * 2)))
            split_components = []
            for i in range(0, len(comp_accounts), chunk_size):
                chunk = comp_accounts[i:i + chunk_size]
                if len(chunk) >= 3:
                    split_components.append(chunk)
            if len(split_components) >= 2:
                components = split_components

        # Build ring payload and keep only rings with at least one beneficiary shared by >=2 accounts.
        suspicious_rings = []
        for comp_accounts in components:
            ben_count = defaultdict(int)
            for acc in comp_accounts:
                for ben in account_to_bens.get(acc, []):
                    ben_count[ben] += 1
            shared_beneficiaries = sorted([ben for ben, c in ben_count.items() if c >= 2])
            if not shared_beneficiaries:
                continue
            suspicious_rings.append(
                {
                    "accounts": comp_accounts,
                    "shared_beneficiaries": shared_beneficiaries,
                    "size": len(comp_accounts),
                }
            )

        # Stable IDs for UI
        suspicious_rings = sorted(suspicious_rings, key=lambda r: (-r["size"], r["accounts"][0]))
        for i, ring in enumerate(suspicious_rings):
            ring["ring_id"] = i

        return suspicious_rings

    def calculate_risk_score(self, account_id):
        """Calculate composite risk score (0-100)."""
        score = 0

        cyber_flags = self.detect_cyber_anomalies(account_id)
        score += len(cyber_flags) * 10

        fin_flags = self.detect_financial_velocity(account_id)
        score += len(fin_flags) * 10

        if account_id in self.graph:
            degree = self.graph.degree(account_id)
            score += min(degree * 2, 30)

        self.risk_scores[account_id] = min(score, 100)
        return self.risk_scores[account_id]

    def get_flagged_accounts(self, threshold=50):
        """Get all accounts above risk threshold."""
        flagged = []
        for account in self.cyber_df["account_id"].unique():
            score = self.calculate_risk_score(account)
            if score >= threshold:
                flagged.append(
                    {
                        "account_id": account,
                        "risk_score": score,
                        "cyber_flags": self.detect_cyber_anomalies(account),
                        "financial_flags": self.detect_financial_velocity(account),
                    }
                )

        return sorted(flagged, key=lambda x: x["risk_score"], reverse=True)


if __name__ == "__main__":
    cyber = pd.read_csv("cyber_events.csv")
    txns = pd.read_csv("transactions.csv")

    detector = CyberFinDetector(cyber, txns)
    detector.build_graph()

    print("\n🔍 Detecting mule rings...")
    rings = detector.detect_mule_rings()
    print(f"Found {len(rings)} suspicious rings")
    for ring in rings[:3]:
        print(f"  Ring {ring['ring_id']}: {ring['size']} accounts → {ring['shared_beneficiaries']}")

    print("\n⚠️  Top 10 high-risk accounts:")
    flagged = detector.get_flagged_accounts(threshold=40)
    for acc in flagged[:10]:
        print(f"  {acc['account_id']}: Risk={acc['risk_score']} | {acc['cyber_flags']} | {acc['financial_flags']}")
