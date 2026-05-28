from api.generator import generate_lyrics, generate_music

lyrics = generate_lyrics(
    recipient_name="Олена",
    occasion="день народження",
    style="pop",
    language="uk",
    details="любить квіти і каву"
)
print("=== ТЕКСТ ===")
print(lyrics)
