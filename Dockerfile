# CyberFin Fusion - Docker Container
# Basic Python 3.13 slim image for 24-hour hackathon demo

FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Generate mock data
RUN python data_generator.py

# Expose Streamlit port
EXPOSE 8501

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Run dashboard with increased upload size
CMD ["streamlit", "run", "dashboard_enhanced.py", "--server.address=0.0.0.0", "--server.maxUploadSize=200"]
