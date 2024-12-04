# KBB Vehicle Data Scraper

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Testing](#testing)
- [Logging](#logging)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Introduction

The KBB Vehicle Data Scraper is a robust and efficient web scraper designed to collect comprehensive vehicle data from Kelley Blue Book (KBB). The scraper extracts detailed information such as make, model, year, price, fuel economy, ratings, and more. This data is then processed and stored in JSON format, ready for analysis or integration into other applications.

This project demonstrates advanced web scraping techniques, including:

- Dynamic pagination handling
- Data caching and retries with exponential backoff
- Intelligent rate limiting to prevent server overload
- Robust exception handling and logging
- Configurable settings for flexibility and scalability
- Comprehensive unit testing to ensure code reliability

## Features

### Comprehensive Data Extraction

Scrapes detailed vehicle information including make, model, year, price, fuel economy, expert and consumer ratings, and descriptions.

### Dynamic Pagination

Automatically navigates through multiple pages until all vehicle data is collected.

### Robust Exception Handling

Implements retries with exponential backoff and detailed logging to handle transient network errors gracefully.

### Configurable Settings

All key parameters are configurable via `config.ini` and `.env` files for flexibility and security.

### Intelligent Rate Limiting

Includes random delays between requests to mimic human behavior and prevent server overload.

### Data Caching

Utilizes caching mechanisms to avoid redundant network requests, improving efficiency.

### Comprehensive Logging

Generates detailed logs for monitoring, debugging, and performance analysis.

### Unit Testing

Includes a suite of unit tests to validate functionality and ensure code reliability.

## Installation

### Prerequisites

- Python 3.9 or higher
- Git (for cloning the repository)

### Steps

1. Clone the repository:
   bash git clone https://github.com/yourusername/kbb-vehicle-data-scraper.git cd kbb-vehicle-data-scraper

2. Create a virtual environment:
   bash python -m venv venv

3. Activate the virtual environment:
   On Windows:
   bash venv\Scripts\activate

On macOS/Linux:
bash source venv/bin/activate

4. Install the required packages:
   bash pip install -r requirements.txt

## Configuration

### Environment Variables (.env)

Create a `.env` file in the project root directory to store sensitive configurations such as proxy settings.

makefile

.env
Proxy configuration (if required)
PROXY_USERNAME=your_proxy_username PROXY_PASSWORD=your_proxy_password PROXY_HOST=your_proxy_host PROXY_PORT=your_proxy_port

### Application Settings (src/config.ini)

The `config.ini` file contains application-specific settings.

ini

src/config.ini
[DEFAULT]

Base URL of the website to scrape
BaseURL = https://www.kbb.com/car-finder/

Path to the data file where scraped data will be saved
DataFilePath = data/kbb_vehicle_data.json

Logging configuration
MaxLogs = 5 LogLevel = INFO

Retry configuration
MaxRetries = 5 BackoffFactor = 0.5

Rate limiting configuration (in seconds)
DelayMin = 20 DelayMax = 60

## Usage

### Running the Scraper

To start the scraper, execute the following command from the project root directory:

bash python src/scraper.py

### Command-Line Options

The scraper will automatically test the proxy connection (if configured) before starting the scraping process.

## Testing

The project includes a suite of unit tests to ensure code reliability.

### Running Tests

From the project root directory, run:

bash python -m unittest discover tests

### Test Coverage

- `tests/test_scraper.py`: Tests the data extraction logic from the HTML content.
- `tests/test_data_processing.py`: Tests data loading, updating, and saving functionalities.
- `tests/test_utils.py`: Tests utility functions such as session creation, proxy configuration, and request handling.

## Logging

Logs are stored in the `logs/` directory. The logging configuration can be adjusted in the `config.ini` file.

- Log Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log Rotation: Keeps a maximum of `MaxLogs` log files before rotating.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Write tests for your changes.
4. Submit a pull request with a detailed description of your changes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Kelley Blue Book (KBB) for providing the vehicle data.
- BeautifulSoup for HTML parsing.
- Requests for HTTP requests.
- CacheTools for caching support.
