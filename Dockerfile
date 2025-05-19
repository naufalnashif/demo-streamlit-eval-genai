FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements dan source
COPY requirements.txt ./
COPY src/ ./src/

# Install dependencies
RUN pip3 install -r requirements.txt

# Create and give permissions to .streamlit and .config folders
RUN mkdir -p /app/.streamlit /app/.config/matplotlib && \
    chmod -R 777 /app/.streamlit /app/.config/matplotlib

# Set environment variables
ENV STREAMLIT_CONFIG_DIR=/app/.streamlit \
    MPLCONFIGDIR=/app/.config/matplotlib \
    STREAMLIT_HOME=/app/.streamlit

# Optional: prevent Streamlit from collecting usage stats
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "src/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]