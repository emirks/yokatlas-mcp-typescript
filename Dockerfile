# Use Node.js 22 slim as base image
FROM node:22-slim

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for python command
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Set working directory
WORKDIR /app

# Copy package files first for better Docker layer caching
COPY package*.json ./
COPY requirements.txt ./

# Install Node.js dependencies
RUN npm ci --only=production

# Install Python dependencies
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install --break-system-packages -r requirements.txt

# Copy source code
COPY . .

# Build the MCP server
RUN npx -y @smithery/cli@1.2.17 build -o .smithery/index.cjs

# Expose port (Smithery will set PORT env var)
EXPOSE $PORT

# Verify installations
RUN echo "Node.js version: $(node --version)" && \
    echo "Python version: $(python3 --version)" && \
    echo "Python location: $(which python3)" && \
    echo "Python symlink: $(which python)"

# Run the built server
CMD ["node", ".smithery/index.cjs"] 