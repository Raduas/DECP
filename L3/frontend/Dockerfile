# =========================================
# Stage: Development (Vite React.js App)
# =========================================
ARG NODE_VERSION=26.1.0-trixie-slim

FROM node:${NODE_VERSION} AS dev

# Set working directory inside the container
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy rest of the source code
COPY . .


# Ensure the "node" user owns the application files
RUN chown -R node:node /app


# Switch to the built-in non-root "node" user
#USER node

# Expose Vite dev server port
EXPOSE 5173

# Run Vite in dev mode, accessible outside the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]