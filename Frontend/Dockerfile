# Use a lightweight Node image
FROM node:22-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the frontend code
COPY . .

# Expose the React development port
EXPOSE 3000

# Start the React development server
CMD ["npm", "start"]