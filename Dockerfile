# Use Node.js 22 slim as base image
FROM node:22-slim

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files first for better Docker layer caching
COPY package*.json ./
COPY requirements.txt ./

# Install Node.js dependencies
RUN npm ci --only=production

# Create Python virtual environment and install dependencies
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

# Set up environment for runtime
ENV PATH="/opt/venv/bin:$PATH"
ENV VIRTUAL_ENV="/opt/venv"

# Copy source code
COPY . .

# Build the MCP server
RUN npx -y @smithery/cli@1.2.17 build -o .smithery/index.cjs

# Expose port (Smithery will set PORT env var)
EXPOSE $PORT

# Verify installations
RUN echo "Node.js version: $(node --version)" && \
    echo "Virtual env contents: $(ls -la /opt/venv/bin/)" && \
    echo "Python version: $(python --version)" && \
    echo "Python3 version: $(python3 --version)" && \
    echo "Python location: $(which python)" && \
    echo "Python3 location: $(which python3)" && \
    echo "Pip version: $(pip --version)" && \
    echo "Virtual env packages: $(pip list)"

# Run the built server
CMD ["node", ".smithery/index.cjs"] 