# Use the smallest possible base image (BusyBox)
# renovate: datasource=docker depName=busybox
FROM busybox:1.37.0-uclibc

# Create the directory for the web files
RUN mkdir -p /www

# Create an entrypoint script that injects the hostname dynamically
COPY ./ep.sh /ep.sh

# Make the script executable
RUN chmod +x /ep.sh

# Expose port 80
EXPOSE 80

# Run the entrypoint script at container startup
CMD ["/ep.sh"]
