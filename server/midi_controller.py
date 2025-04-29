import mido
import time
import re # Add regex import for note parsing

# --- Constants ---
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
BASE_OCTAVE = 4 # Middle C (C4) is MIDI note 60

# --- Helper Functions ---

def note_name_to_midi(note_name):
    \"\"\"Converts a note name (e.g., 'C4', 'F#5') to a MIDI note number.\"\"\"
    match = re.match(r'([A-G]#?)(\d+)', note_name.upper())
    if not match:
        raise ValueError(f"Invalid note name format: {note_name}")

    name, octave_str = match.groups()
    octave = int(octave_str)

    try:
        note_index = NOTE_NAMES.index(name)
    except ValueError:
        raise ValueError(f"Invalid note name: {name}")

    # MIDI note number calculation: C4 = 60
    midi_note = 12 * octave + note_index
    return midi_note

def build_major_triad(root_midi_note):
    \"\"\"Builds a major triad (root, major third, perfect fifth) from a root MIDI note.\"\"\"
    # Major third is 4 semitones up
    major_third = root_midi_note + 4
    # Perfect fifth is 7 semitones up
    perfect_fifth = root_midi_note + 7
    return [root_midi_note, major_third, perfect_fifth]

# Function to list available MIDI output ports
def list_midi_outputs():
    print("Available MIDI output ports:")
    for name in mido.get_output_names():
        print(name)

# Function to open a MIDI output port
def open_midi_output(port_name=None):
    try:
        if port_name:
            outport = mido.open_output(port_name)
            print(f"Opened MIDI output port: {port_name}")
        else:
            outport = mido.open_output() # Open the default output port
            print(f"Opened default MIDI output port: {outport.name}")
        return outport
    except OSError as e:
        print(f"Error opening MIDI port: {e}")
        print("Please ensure a MIDI device is connected or a virtual MIDI port is running.")
        print("Available ports:")
        list_midi_outputs()
        return None

# --- Main Playing Logic ---
def play_sequence(outport, sequence_data):
    if not outport:
        print("MIDI output port is not open. Cannot play sequence.")
        return

    notes = sequence_data.get('notes', [])
    two_hands = sequence_data.get('two_hands', False)
    play_duration = sequence_data.get('duration', 0.5) # Default duration 0.5s
    velocity = sequence_data.get('velocity', 64)      # Default velocity
    melody_octave_shift = 1 # Play melody notes 1 octave higher (e.g., C4 input -> C5 played)
    chord_octave_shift = -1 # Play chords 1 octave lower (e.g., C4 input -> C3 chord root)

    if not notes:
        print("No notes provided in the sequence.")
        return

    print(f"Playing sequence: {notes}, Two Hands: {two_hands}, Duration: {play_duration}s")

    for note_name in notes:
        try:
            base_midi_note = note_name_to_midi(note_name)
        except ValueError as e:
            print(f"Skipping invalid note: {e}")
            continue

        notes_on = []
        msgs_on = []
        msgs_off = []

        # --- Determine notes to play ---
        melody_note = base_midi_note + (12 * melody_octave_shift)
        notes_on.append(melody_note)

        if two_hands:
            chord_root_note = base_midi_note + (12 * chord_octave_shift)
            chord_notes = build_major_triad(chord_root_note)
            notes_on.extend(chord_notes)
            # Optional: Avoid playing the melody note if it's already in the low chord
            # notes_on = list(set(notes_on)) # Using set removes duplicates

        # --- Create MIDI messages ---
        for note in notes_on:
            # Ensure notes are within valid MIDI range (0-127)
            if 0 <= note <= 127:
                msgs_on.append(mido.Message('note_on', note=note, velocity=velocity))
                msgs_off.append(mido.Message('note_off', note=note, velocity=0))
            else:
                print(f"Warning: Note {note} is outside MIDI range (0-127) and will be skipped.")

        # --- Send MIDI messages ---
        if msgs_on:
            print(f"Sending ON: {[msg.note for msg in msgs_on]}")
            for msg in msgs_on:
                outport.send(msg)

            time.sleep(play_duration)

            print(f"Sending OFF: {[msg.note for msg in msgs_off]}")
            for msg in msgs_off:
                outport.send(msg)
        else:
            # If no valid notes were generated, still wait to keep rhythm
             time.sleep(play_duration)

# --- Main execution part (example usage) ---
if __name__ == "__main__":
    list_midi_outputs()
    output_port = open_midi_output()

    if output_port:
        # Example 1: Simple melody (C4, E4, G4 played as C5, E5, G5)
        print("\n--- Playing Simple Melody ---")
        melody_sequence = {
            "notes": ["C4", "E4", "G4", "C5"],
            "duration": 0.4,
            "velocity": 70
        }
        play_sequence(output_port, melody_sequence)
        time.sleep(1)

        # Example 2: Two-handed playing (Melody C4, E4, G4 -> played as C5, E5, G5; Chords C3, E3, G3)
        print("\n--- Playing Two Hands ---")
        two_hand_sequence = {
            "notes": ["C4", "E4", "G4", "C5"],
            "two_hands": True,
            "duration": 0.6,
            "velocity": 60
        }
        play_sequence(output_port, two_hand_sequence)
        time.sleep(1)

        # Example 3: Two-handed with higher notes (Melody G5, A5; Chords G4, A4)
        print("\n--- Playing Two Hands - Higher Notes ---")
        higher_two_hand_sequence = {
            "notes": ["G5", "A5", "G5"],
            "two_hands": True,
            "duration": 0.5,
            "velocity": 75
        }
        play_sequence(output_port, higher_two_hand_sequence)
        time.sleep(1)

        # Close the port when done
        print("\nClosing MIDI port.")
        output_port.close()
    else:
        print("Could not open MIDI port. Exiting.") 