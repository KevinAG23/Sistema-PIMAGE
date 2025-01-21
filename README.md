# Secure Image Upload System

This project is a web-based system for securely uploading, analyzing, moderating, and displaying images. It includes features for preventing steganography and ensuring that uploaded images comply with moderation policies before they are displayed in the public gallery.

## Features

- **Secure Image Upload**: Allows users to upload images anonymously with unique aliases.
- **Steganography Analysis**: Automatically detects hidden data or metadata in uploaded images to prevent steganographic exploits.
- **Moderation System**: Enables administrators to approve or reject images before publishing them in the gallery.
- **Public Gallery**: Displays only approved and safe images.
- **Pending Review List**: Lists images pending moderation for administrative review.
- **RESTful API**: Fully implemented API endpoints for image upload, moderation, and gallery management.

## Tech Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) - Python web framework for building APIs.
- **Database**: PostgreSQL - Relational database for storing image metadata and moderation statuses.
- **Steganography Detection**: [Stegano](https://pypi.org/project/stegano/) - Library for analyzing hidden data in images.
- **File Type Validation**: [python-magic](https://pypi.org/project/python-magic/) - For detecting MIME types of uploaded files.
- **Image Processing**: [Pillow (PIL)](https://pypi.org/project/Pillow/) - For image metadata extraction and validation.
- **Docker**: Containerized deployment of the application and database.

## Requirements

- Python 3.8+
- PostgreSQL 12+
- Docker (optional for containerized deployment)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/secure-image-upload.git
   cd secure-image-upload
