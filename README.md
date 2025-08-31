# TYT-MD-UV380-OpenGD-CSV-Converter

A powerful tool to convert CSV Digital Contacts and Channels from TYT, Retevis, and Baofeng radios into OpenGD77 compatible formats.

## ✨ Features

- **Multi-format Support**: Converts CSV files from TYT MD-UV380/390, Retevis RT3S, Baofeng DM-1701
- **Contact Sources**: Supports TYT Digital Contacts and DC9AL ContactLists from GitHub
- **Preview & Select Interface**: Interactive checkbox-based selection with visual feedback
- **Advanced Filtering**: Search and filter contacts/channels while preserving selections
- **Smart Limit Management**: Enforces OpenGD77's 1024 contact limit with visual warnings
- **Real-time Counting**: Accurate counters showing filtered vs. total selections
  
<img width="804" height="653" alt="image" src="https://github.com/user-attachments/assets/fdc7a999-1219-4520-977c-0b64302a7744" />

## 🚀 Quick Start

### Option 1: Download Executable (Recommended)
1. Download the latest `OpenGD77_Converter.exe` from [Releases](../../releases)
2. Run the executable - no installation required!
3. Load your CSV files and start converting

### Option 2: 🔧 Run from Source

1. Clone the repository.
2. Install requirements:
pip install -r requirements.txt
3. Launch the app:
python main.py


## 📖 How to Use

### Basic Workflow
1. **Load Files**: Click "Browse" to select your TYT/Retevis CSV files

2. **Preview & Select**: The preview window opens automatically
   - Browse all contacts and channels in tabbed interface
   - Use checkboxes or double-click rows to select items

3. **Search & Filter**:
   - Search by name using the search box
   - Filter by type (Group/Private for contacts, Analogue/Digital for channels)
   - Your selections are preserved across all filters

4. **Export**: Click "Import Selected" to generate OpenGD77 CSV files

### Advanced Selection Features
- **Individual Selection**: Click checkbox or double-click any row
- **Bulk Selection**: Use "Select All Visible" to add filtered items to existing selection
- **Global Management**: "Deselect All" clears everything

## Supported File Formats

### Input Formats
| Radio Model | File Type | Description |
|-------------|-----------|-------------|
| **TYT MD-UV380/390** | Digital Contacts CSV | Contact list with Call ID and Call Type |
| **TYT MD-UV380/390** | Channels CSV | Channel list with frequencies and settings |
| **Retevis RT3S** | Digital Contacts CSV | Compatible with TYT format |
| **Retevis RT3S** | Channels CSV | Compatible with TYT format |
| **Baofeng DM-1701** | CSV Files | Compatible with TYT format |
| **[DC9AL ContactLists](https://github.com/ContactLists)** | CSV from GitHub | GD77 format |



## **🆘 Support & Help**
Issues: Use the GitHub Issues page for bug reports

Questions: Check existing issues or create a new one

Feature Requests: Welcome via GitHub Issues

## **⭐ Show Your Support**
If this tool helps you program your OpenGD77 radio, please:

⭐ Star this repository
🐛 Report bugs you find
💡 Suggest improvements
📢 Share with fellow hams



73 DE IT9KVB 📻



This tool is developed by and for the amateur radio community. Use responsibly and according to your local radio regulations.
