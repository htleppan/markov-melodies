# Markov Melodies

Python script for extracting chord transition probabilities from given MIDI files. Uses [Mido](https://github.com/mido/mido) for parsing MIDI files.

Demo live at https://htleppan.github.io/markov-melodies/index.html

Usage: `python midi2mc.py [file1.mid] [file2.mid]`

Outputs a .json file:

```
[
   {
    "tempo": 375000,	  // microseconds per 4th note
    "signature": [4, 4],

// Chord lookup table
    "chords": 
      [
        {"notes": [28, 40, 76, 88], "fraction": 8}, 
        {"notes": [52, 55, 59], "fraction": 4}, 
           ...
      ],

// Transition probabilities
     "transition_list":
      [
       [[[1], [1.0]],		// p(chords[1]  | chords[0]) = 1.0
        [[2, 62], [0.5, 0.5]],  // p(chords[2]  | chords[1]) = 0.5 
                                // p(chords[62] | chords[1]) = 0.5 
            ...
      ]
```
