# ClockIt Desktop Application

## Development Setup

1. Install Node.js and npm
2. Install dependencies:
   ```bash
   cd electron
   npm install
   ```

## Running in Development

```bash
cd electron
npm run dev
```

This will start the Electron app in development mode, which will look for the Python backend in the parent `src` directory.

## Building for Production

1. First, ensure you have a compiled backend:
   ```bash
   cd ..
   python build.py
   ```

2. Copy the backend executable to the electron directory:
   ```bash
   mkdir -p electron/backend
   cp releases/latest/clockit electron/backend/
   ```

3. Build the Electron app:
   ```bash
   cd electron
   npm run build
   ```

## Available Scripts

- `npm start` - Start the application
- `npm run dev` - Start in development mode
- `npm run build` - Build for all platforms
- `npm run build-win` - Build for Windows
- `npm run build-mac` - Build for macOS
- `npm run build-linux` - Build for Linux

## Features

- Native desktop application
- Professional UI with the existing web interface
- Menu bar with keyboard shortcuts
- System tray integration (planned)
- Native notifications
- Desktop-specific optimizations
- Data stored in user's app data directory
