#!/bin/bash

# Update package list and install necessary tools
sudo apt update
sudo apt install -y software-properties-common

# Add the repository for Python 3.10 and update package list
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.10 and necessary packages
sudo apt install -y python3.10 python3.10-venv python3.10-dev

# Install pip for Python 3.10
curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.10

# Create and activate a virtual environment
python3.10 -m venv myenv
source myenv/bin/activate

# Install PyArmor within the virtual environment
pip install pyarmor

# Path for the PyArmor registration file
REGISTRATION_FILE="/home/ubuntu/pyarmor-regfile-4556.zip"

# Check if the registration file exists
if [[ -f "$REGISTRATION_FILE" ]]; then
  echo "Registration file found: $REGISTRATION_FILE"
  echo "Using existing registration file to register PyArmor..."

  # Register PyArmor using the registration file
  pyarmor reg "$REGISTRATION_FILE"

  # Check if the registration was successful
  if [[ $? -ne 0 ]]; then
    echo "Error: PyArmor registration failed. Please check your registration file."
    exit 1
  fi

  # Confirm registration and check PyArmor version
  echo "Checking PyArmor version and registration status..."
  pyarmor -v

  echo "PyArmor registration completed successfully."
else
  echo "Error: Registration file not found: $REGISTRATION_FILE"
  exit 1
fi

# Prompt for GitHub repository URL (including https://)
read -p "Enter the full GitHub repository URL (with https://): " GIT_REPO

# Prompt for GitHub username
read -p "Enter your GitHub username: " GIT_USERNAME

# Prompt for GitHub personal access token (PAT) securely
read -sp "Enter your GitHub personal access token (PAT): " GIT_PAT
echo

# Extract the repository name from the GIT_REPO URL
REPO_NAME=$(basename "$GIT_REPO" .git)

# Check if the directory exists
if [ -d "$REPO_NAME" ]; then
  echo "Directory '$REPO_NAME' already exists. Removing it..."
  rm -rf "$REPO_NAME"
fi

# Clone the repository with authentication using Git PAT
echo "Cloning repository..."
git clone "https://$GIT_USERNAME:$GIT_PAT@${GIT_REPO#https://}"

# Check if the clone was successful
if [[ $? -ne 0 ]]; then
  echo "Error: Failed to clone repository. Please check your credentials."
  exit 1
fi

# Change to the project directory
cd "$REPO_NAME" || { echo "Error: Directory not found."; exit 1; }

# Display current branches
git branch

# Create new branch 'onprem' and switch to it
git checkout -b onprem

# Create 'pyarmor' branch from 'onprem' and switch to it
git checkout -b pyarmor origin/onprem

# Initialize PyArmor with the entry point
pyarmor-7 init --entry=manage.py

# Build the project with PyArmor
pyarmor-7 build

# Git operations
#git rm --cached dist
rm -rf dist/.git
git add dist
git commit -m "Convert dist to a regular folder"
git push origin pyarmor

# Ensure extended globbing is enabled
shopt -s extglob

# Remove all directories except dist
rm -rf !(dist)

# Move all files from dist to the current directory
mv dist/* .

# Remove the dist directory
rm -rf dist/
git add .
git commit -m "Add files from dist folder to new branch"
git push origin pyarmor

echo "Script execution completed successfully."