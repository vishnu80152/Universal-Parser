import asyncio
from pydoc import text
from Extractor.online_ext import WebCrawlerService
from Extractor.audio_ext import AudioTranscriber

async def transcribe_audio(file_path: str): 
    transcriber = AudioTranscriber(
        model_size="base",
        device="cpu",
    )
    transcript = transcriber.transcribe(audio_path=file_path)
    return transcript

async def crawl(url: str = None):
    # Initialize crawler service
    crawler = WebCrawlerService(
        headless=True,
        verbose=True,
    )
    # URL to crawl
    # Call crawler
    result = await crawler.crawl(
        url=url,
        filter_type="bm25",   # or "bm25"
        threshold=0.48,
    )
    # Access results
    raw_md = result["raw_markdown"]
    fit_md = raw_md
    
    # fit_md = result["fit_markdown"]
    # print("Raw markdown length:", result["raw_length"])
    # print("Filtered markdown length:", result["fit_length"])
    # print("\n--- Preview (first 500 chars) ---\n")
    # print(fit_md[:500])
    # Optional: save to file
    return fit_md    
    


if __name__ == "__main__":
    # url = "https://docs.micronaut.io/4.9.9/guide/"    
    # data = asyncio.run(crawl(url=url))
    # with open("output.md", "w", encoding="utf-8") as f:
    #     f.write(data)
        
    audio_path = "/home/zoro/DEV/chatbot/sample_data/harvard.wav"
    text = asyncio.run(transcribe_audio(file_path=audio_path))
    print(text["text"])