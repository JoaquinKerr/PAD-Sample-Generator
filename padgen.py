#!/usr/bin/env python3
# A simple implementation of the PAD Synthesis algorithm
# Found here:  https://zynaddsubfx.sourceforge.io/doc/PADsynth/PADsynth.htm


import wave
import numpy as np
import os, random, math


# Profile function 
def profile(fi: float, bwi: float) -> float:
    x = fi / bwi
    x *= x
    if x > 14.71280603:
        return 0.0
    return np.exp(-x) / bwi


def do_the_thing():
    # Configuration
    samplerate = 48000.0
    numFrames = pow(2,16) # 15 or 16 are good sizes, 16 is minimum for 55 hz Base F
    half_size = numFrames // 2 + 1
    stereo = True

    # 4, 110, and 45 are good values for most sounds
    # 5, 55, and 33 are better for sounds that are really rich and go low
    numSamples = 4 # How many ocataves to generate samples for
    BaseF = 110.0 # Base Frequency for the algo
    BaseMidiNoteNum = 45 # 33 + 12


    # Input vars
    BW = 16         # Bandwidth of first Harmonic, 5 to 50 is normal
    BW_SCALE = 1.45  # Bandwidth scaling, 1 to 2.5 is normal

    # Harmonics table
    # Here's where the sounds spectrum is set up
    # Doesn't have to be 64, but it's a good for most uses.

    # harms = np.zeros(64)
    harms = np.random.rand(64)
    harms = np.where(harms > 0.9, 1.0, 0.0)
    # harms *= np.linspace(1.0, 0, 64)
               
    harms[0] = 0 # Not used
    harms[1] = 1 # Root


    # **************************************************************
    #Make output dir
    i = 1
    while os.path.exists(f"Sound_{i}"):
        i += 1

    pth = f"Sound_{i}\\"
    os.mkdir(pth)


    #Make samples
    for octave in range(numSamples):
        F = BaseF * (2 ** octave)

        amps = np.zeros(half_size)
        phases = np.random.rand(half_size) * 2 * np.pi

        h = 1
        while h < len(harms):
            bw_Hz = (pow(2.0, BW / 1200.0) - 1.0) * F * pow(h, BW_SCALE)
            bwi = bw_Hz / (2.0 * samplerate)
            fi = F * h / samplerate

            i = 0
            while i < (numFrames // 2):
                hprofile = profile((i / numFrames) - fi, bwi)
                amps[i] = amps[i] + hprofile * harms[h]
                i += 1
            h += 1

        complex_half = amps * (np.cos(phases) + 1j * np.sin(phases))
        left_channel = np.fft.irfft(complex_half, numFrames)
        left_channel /= np.max(np.abs(left_channel))
        numChan = 0
        if stereo:
            right_channel = np.roll(left_channel, numFrames // 2)
            audio = np.array([left_channel, right_channel]).T
            audio = (audio * (2**15 - 1)).astype("<h")
            numChan = 2
        else:
            audio = (left_channel * (2**15 - 1)).astype("<h")
            numChan = 1

        outfile = pth + f"wav_{int(F)}.wav"
        with wave.open(outfile, "wb") as f:
            f.setnchannels(numChan)
            f.setsampwidth(2)
            f.setframerate(samplerate)
            f.writeframes(audio.tobytes())
            print(f"* {outfile} written")

    #Make sfz file
    with open(pth + "padgen.sfz", "w") as f:
        f.write("<control>\n<global>\n<group>\nloop_mode=loop_continuous\n\n")

        for r in range(numSamples):
            kc = BaseMidiNoteNum+12 * r
            lk = 1 if r == 0 else kc-5
            hk = 127 if r == numSamples-1 else kc+6
            ff = int(BaseF * (2 ** r))
            f.write(f"<region> sample=wav_{ff}.wav lokey={lk} hikey={hk} pitch_keycenter={kc}\n")


    print("Pad Export Done")


if __name__ == "__main__":
    do_the_thing()
