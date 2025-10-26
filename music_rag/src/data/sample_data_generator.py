"""Generate sample music dataset for testing."""

from typing import List
from ..models.music_item import MusicItem, MusicMetadata
import json


def generate_sample_music_data() -> List[MusicItem]:
    """Generate a diverse sample music dataset."""

    samples = [
        # Western Classical
        MusicItem(
            id="1",
            title="Symphony No. 9",
            artist="Ludwig van Beethoven",
            description="Epic symphony featuring the famous 'Ode to Joy' theme",
            metadata=MusicMetadata(
                genre="Classical",
                subgenre="Symphony",
                cultural_origin="German",
                tempo=120.0,
                key="D minor",
                time_signature="4/4",
                instrumentation=["orchestra", "choir"],
                mood=["triumphant", "powerful", "emotional"],
                era="Romantic",
                duration=4200.0
            )
        ),

        # Jazz
        MusicItem(
            id="2",
            title="So What",
            artist="Miles Davis",
            description="Modal jazz masterpiece with cool, laid-back vibe",
            metadata=MusicMetadata(
                genre="Jazz",
                subgenre="Modal Jazz",
                cultural_origin="American",
                tempo=138.0,
                key="D Dorian",
                instrumentation=["trumpet", "saxophone", "piano", "bass", "drums"],
                mood=["cool", "sophisticated", "relaxed"],
                era="1950s",
                duration=542.0
            )
        ),

        # Indian Classical
        MusicItem(
            id="3",
            title="Raga Yaman",
            artist="Ravi Shankar",
            description="Traditional Indian raga emphasizing serenity and devotion",
            metadata=MusicMetadata(
                genre="Indian Classical",
                subgenre="Hindustani",
                cultural_origin="Indian",
                tempo=80.0,
                instrumentation=["sitar", "tabla", "tanpura"],
                mood=["meditative", "serene", "spiritual"],
                era="1960s",
                duration=1800.0
            )
        ),

        # West African
        MusicItem(
            id="4",
            title="Djembe Celebration",
            artist="Mamady Keïta",
            description="Energetic West African drumming with complex polyrhythms",
            metadata=MusicMetadata(
                genre="World Music",
                subgenre="West African Percussion",
                cultural_origin="Guinean",
                tempo=140.0,
                instrumentation=["djembe", "dundun", "kenkeni"],
                mood=["energetic", "celebratory", "rhythmic"],
                is_live_performance=True,
                duration=480.0
            )
        ),

        # Electronic
        MusicItem(
            id="5",
            title="Strobe",
            artist="deadmau5",
            description="Progressive house track with emotional build-ups",
            metadata=MusicMetadata(
                genre="Electronic",
                subgenre="Progressive House",
                cultural_origin="Canadian",
                tempo=128.0,
                key="C# minor",
                time_signature="4/4",
                instrumentation=["synthesizer", "drum machine"],
                mood=["uplifting", "emotional", "energetic"],
                era="2000s",
                duration=636.0
            )
        ),

        # Middle Eastern
        MusicItem(
            id="6",
            title="Maqam Hijaz",
            artist="Omar Faruk Tekbilek",
            description="Turkish/Arabic music featuring quarter-tone scales",
            metadata=MusicMetadata(
                genre="Middle Eastern",
                subgenre="Turkish Classical",
                cultural_origin="Turkish",
                tempo=90.0,
                instrumentation=["ney", "oud", "darbuka"],
                mood=["mystical", "contemplative", "exotic"],
                duration=420.0
            )
        ),

        # Rock
        MusicItem(
            id="7",
            title="Bohemian Rhapsody",
            artist="Queen",
            description="Rock opera epic with operatic and hard rock sections",
            metadata=MusicMetadata(
                genre="Rock",
                subgenre="Progressive Rock",
                cultural_origin="British",
                tempo=72.0,
                key="B♭ major",
                time_signature="4/4",
                instrumentation=["vocals", "guitar", "bass", "drums", "piano"],
                mood=["dramatic", "theatrical", "powerful"],
                era="1970s",
                duration=354.0
            )
        ),

        # Brazilian
        MusicItem(
            id="8",
            title="The Girl from Ipanema",
            artist="Stan Getz & João Gilberto",
            description="Bossa nova classic with smooth samba rhythm",
            metadata=MusicMetadata(
                genre="Latin",
                subgenre="Bossa Nova",
                cultural_origin="Brazilian",
                tempo=120.0,
                key="F major",
                instrumentation=["saxophone", "guitar", "vocals", "bass", "drums"],
                mood=["relaxed", "romantic", "sunny"],
                era="1960s",
                duration=318.0
            )
        ),

        # Live Performance
        MusicItem(
            id="9",
            title="Comfortably Numb (Live)",
            artist="Pink Floyd",
            description="Live stadium performance with extended guitar solos",
            metadata=MusicMetadata(
                genre="Rock",
                subgenre="Progressive Rock",
                cultural_origin="British",
                tempo=63.0,
                instrumentation=["guitar", "bass", "drums", "keyboards", "vocals"],
                mood=["epic", "atmospheric", "powerful"],
                era="1980s",
                is_live_performance=True,
                venue="Earl's Court, London",
                audience_response="Enthusiastic",
                duration=720.0
            )
        ),

        # Hip Hop
        MusicItem(
            id="10",
            title="N.Y. State of Mind",
            artist="Nas",
            description="East Coast hip hop with jazz-influenced production",
            metadata=MusicMetadata(
                genre="Hip Hop",
                subgenre="East Coast Hip Hop",
                cultural_origin="American",
                tempo=85.0,
                instrumentation=["drums", "piano", "bass", "samples"],
                mood=["gritty", "introspective", "urban"],
                era="1990s",
                lyrics="Vivid street poetry about life in New York",
                duration=294.0
            )
        ),
    ]

    return samples


def save_sample_data(output_path: str = "./data/sample_music_dataset.json"):
    """Save sample dataset to JSON file."""
    samples = generate_sample_music_data()

    data = [
        {
            "id": item.id,
            "title": item.title,
            "artist": item.artist,
            "description": item.description,
            "metadata": item.metadata.dict()
        }
        for item in samples
    ]

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(samples)} sample music items to {output_path}")


if __name__ == "__main__":
    save_sample_data()
