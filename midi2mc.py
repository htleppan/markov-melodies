import mido
import math
import numpy as np
import codecs, json 
import sys

if len(sys.argv) == 1:
	print("usage: python midi2mc.py [file1] [file2] ... ")
	sys.exit()


chord_list = []

# Loop through all input files
for filename in sys.argv[1:]:
	mid = mido.MidiFile(filename)

	# Default values for the midi file
	pulses_per_128n = mid.ticks_per_beat * 4 / 128
	tempo = 120
	time_signature = [4, 4]

	note_messages = []
	for message in mido.merge_tracks(mid.tracks):
		if message.is_meta and message.type == "set_tempo":
				tempo = message.dict()['tempo']
		if message.is_meta and message.type == "time_signature":
				time_signature = [message.dict()['numerator'], message.dict()['denominator']]
		if message.type == "note_on" or message.type == "note_off":
			note_messages.append(message)

	# Extract notes and their durations
	# e.g. song_notes[3] = {"time": 134430, "note": 120, "fraction": 8}
	song_notes = []
	elapsed_time = 0
	for m_i in np.arange(0, len(note_messages)):
		msg = note_messages[m_i]
		elapsed_time += msg.time

		if msg.type == "note_on" and msg.velocity != 0:
			note_end_time = elapsed_time
			note_duration = 0

			# Find the ending message (note_off or note_on) and calculate note duration
			for m_j in np.arange(m_i + 1, len(note_messages)):
				note_end_time += note_messages[m_j].time
				if msg.note == note_messages[m_j].note:
					note_duration = note_end_time - elapsed_time
					break
			if note_duration == 0:
				continue
			
			note_frac = round((1 / ((note_duration / pulses_per_128n) * (1 / 128))))
			if note_frac > 128:
				continue
			if note_frac < 1:
				note_frac = 128
			song_notes.append({"time": elapsed_time, "note": msg.note, "fraction": note_frac})

	# Build chords
	# e.g. song_chords["time"] = {notes: [120, 121, 122], fraction: 8  }
	song_chords = {}	
	for n_i in np.arange(0, len(song_notes)):
		note = song_notes[n_i]
		t = note["time"]
		del note["time"]

		if(t in song_chords):
			song_chords[t]["notes"].append(note["note"])
			song_chords[t]["notes"].sort()

			# Shortest note in chord wins
			if(song_chords[t]["fraction"] < note["fraction"]):
				song_chords[t]["fraction"] = note["fraction"]
		else:
			song_chords[t] = {"notes": [note["note"]], "fraction": note["fraction"]}

	# Append built chords to ordered global chord list
	for t, c in song_chords.items():
		chord_list.append(c)

# Build chord lookup table:
# e.g., chord_lookup[3] = {"notes". [120, 122, 123], "fraction": 8}
chord_lookup = []
for c in chord_list:
	if c not in chord_lookup:
		chord_lookup.append(c)

# Calculate transition table - element indices refer to indices in chord lookup table
transition_table = np.zeros((len(chord_lookup), len(chord_lookup)))
for c_i in np.arange(0, len(chord_list) - 1):
	this_chord_idx = chord_lookup.index(chord_list[c_i])
	next_chord_idx = chord_lookup.index(chord_list[c_i + 1])
	transition_table[this_chord_idx][next_chord_idx] += 1

# Fix last chord to uniform transition (otherwise Inf transition probability)
transition_table[len(chord_lookup) - 1, :] = 1

# Normalize transition table
transition_table /= transition_table.sum(axis=1, keepdims=True)

# Extract only non-zero transitions for the json output
transition_list = []
for i in np.arange(0, transition_table.shape[0]):
	nz = np.nonzero(transition_table[i, :])[0]
	c = transition_table[i, nz]
	transition_list.append([nz.tolist(), c.tolist()])

# Export JSON
json_data = []
json_data.append({'tempo': tempo, 'signature': time_signature, 'chords': chord_lookup, 'transition_list': transition_list})
file_path = "transition_probabilities.json"
json.encoder.FLOAT_REPR = lambda o: format(o, '.2f')
json.dump(json_data, codecs.open(file_path, 'w', encoding='utf-8'))

