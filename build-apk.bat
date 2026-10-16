@echo off
echo ========================================================
echo  Building Audio Converter Mobile APK (No Studio Needed)
echo ========================================================

set "JAVA_HOME=C:\Program Files\Java\jdk-21"
set "ANDROID_HOME=H:\android-sdk"
set "PATH=%JAVA_HOME%\bin;%ANDROID_HOME%\platform-tools;%PATH%"

echo [1/3] Building frontend assets...
cd /d "H:\audio converter\frontend"
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo Frontend build failed!
    pause
    exit /b %ERRORLEVEL%
)

echo [2/3] Syncing Capacitor native files...
call npx cap sync
if %ERRORLEVEL% NEQ 0 (
    echo Capacitor sync failed!
    pause
    exit /b %ERRORLEVEL%
)

echo [3/3] Compiling Android APK...
cd /d "H:\audio converter\frontend\android"
call "H:\android-sdk\gradle-8.14.3\bin\gradle.bat" assembleDebug
if %ERRORLEVEL% NEQ 0 (
    echo APK compilation failed!
    pause
    exit /b %ERRORLEVEL%
)

copy /y "H:\audio converter\frontend\android\app\build\outputs\apk\debug\app-debug.apk" "H:\audio converter\AudioConverter-app.apk"

echo ========================================================
echo  SUCCESS! APK generated at:
echo  H:\audio converter\AudioConverter-app.apk
echo ========================================================
pause
