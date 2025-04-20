# NIKKE Data Collector

_[中文版本](README.zh-CN.md)_

## Introduction

NIKKE Data Collector is an automated data collection tool specifically designed for the Arena mode in NIKKE. It automatically records and analyzes match information from the Arena, helping players understand current competitive trends and changes. By collecting participants' lineup configurations, win/loss records, and battle data, players can gain valuable insights about the current game meta and powerful team compositions.

## Features

- Collect data from all tournament rounds (64→32, 32→16, 16→8, 8→4, 4→2, 2→1)
- Automatically detect and record player lineups
- Save data in structured format for further analysis
- Resize game window to optimal dimensions for data collection
- User-friendly interface with progress tracking

## Requirements

- Windows11 operating system
- Python 3.11 or higher
- PySide6 (Qt for Python)
- OpenCV for image recognition
- Administrator privileges (required because NIKKE runs with admin rights; without equal privileges, the application cannot control the game window)

## Installation

1. Clone the repository:

    ```
    git clone https://github.com/username/nikke-data-collector.git
    cd nikke-data-collector
    ```

2. Install dependencies:

    ```
    poetry install
    ```

3. Build
    ```
    poetry run build-release
    ```

## Running

**Important Note**: This application must be run with administrator privileges, otherwise it cannot control the NIKKE game window. The program will check for admin rights at startup and will prompt and exit if they are not granted.

## Usage

1. Start NIKKE and navigate to the Arena Tournament section
2. Select a data collection task in the application
3. Choose a directory to save the collected data
4. Click "Link Start" to begin data collection
5. The application will automatically navigate through the tournament UI and collect data

## License

Licensed under the MIT License

- Permission is granted to use, copy, modify, and distribute this software
- Both commercial and non-commercial use is allowed
- See the LICENSE file for full details

## Disclaimer

This tool is not affiliated with Shift Up or the official NIKKE game. NIKKE and all related properties are trademarks of
their respective owners.

This software is for personal learning and research purposes only. Users must comply with relevant laws and game service
terms. The developers are not responsible for any account issues or losses that may result from using this software.
