import multiprocessing
from bot import main as bot_main
from web_panel import app

def run_bot():
    bot_main()

def run_web_panel():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    # Create processes for bot and web panel
    bot_process = multiprocessing.Process(target=run_bot)
    web_process = multiprocessing.Process(target=run_web_panel)

    # Start both processes
    bot_process.start()
    web_process.start()

    try:
        # Wait for processes to complete
        bot_process.join()
        web_process.join()
    except KeyboardInterrupt:
        print("\nShutting down...")
        # Terminate processes gracefully
        bot_process.terminate()
        web_process.terminate()
        # Wait for processes to terminate
        bot_process.join()
        web_process.join()
        print("Successfully shut down both services.")