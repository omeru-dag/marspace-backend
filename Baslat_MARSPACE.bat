@echo off
title MARSPACE OTONOM KOMUTA MERKEZI BASLATICISI
color 0A

echo ==================================================================
echo.
echo           MARSPACE - ULUSAL KRITIK ALTYAPI KORUMA MERKEZI
echo               OTONOM KRIZ YONETIM PANELI BASLATICISI
echo.
echo ==================================================================
echo.

echo [+] 1. LM Studio Otonom LLM Motoru (Port 1234) Baslatiliyor...
start "MARSPACE - LM Studio (LLM)" cmd /k "title LM Studio Server && lms server start"
timeout /t 3 >nul

echo [+] 2. YOLOv8 Otonom Gorsel Analiz Motoru (Video Stream Port 5006) Baslatiliyor...
start "MARSPACE - Video Stream (YOLOv8)" cmd /k "title Video Stream Server && python stream_loop.py"
timeout /t 1 >nul

echo [+] 3. Telsiz Proxy ve Edge-TTS Sunucusu (Port 5500) Baslatiliyor...
start "MARSPACE - Local Proxy (Port 5500)" cmd /k "title Proxy Server && python proxy.py"
timeout /t 1 >nul

echo [+] 4. Whisper Ses Tanima Motoru (Sesli Komut - Port 8080) Kontrol Ediliyor...
if exist "whisper_bin\Release\whisper-server.exe" (
    start "MARSPACE - Whisper AI (Port 8080)" cmd /k "title Whisper Server && cd whisper_bin\Release && whisper-server.exe -m ggml-base.bin --port 8080"
    echo    - Whisper sunucusu baslatildi.
) else (
    echo    [!] UYARI: 'whisper-server.exe' bulunamadi!
    echo    [!] Lutfen 'python download_whisper.py' calistirarak kurulumu tamamlayin. Cihaz sesli komut alamaz!
)
timeout /t 2 >nul

echo.
echo [+] 5. Sistem hazirliklari tamamlandi, Komuta Arayuzu tarayicida aciliyor...
timeout /t 2 >nul
start index.html

echo.
echo ==================================================================
echo TUM SISTEMLER BASLATILDI! 
echo.
echo Acilan siyah CMD konsol pencerelerini KAPATMAYIN. Bu pencereler
echo arkaplan yapay zeka ve sunucu islemlerini yurutmektedir.
echo Cikmak istediginizde pencereleri kapatabilirsiniz.
echo ==================================================================
pause
