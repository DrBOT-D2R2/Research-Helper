import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from backend.app.pipeline import extract_concepts

# Expanded physics text to generate more relationships
WAVES_TEXT = """
A standing wave, also known as a stationary wave, is a wave that oscillates in time but whose peak amplitude profile does not move in space. 
The peak amplitude of the wave oscillations at any point in space is constant with time, and the oscillations at different points throughout the wave are in phase. 
The locations at which the absolute value of the amplitude is minimum are called nodes, and the locations where the absolute value of the amplitude is maximum are called antinodes.

A standing wave can be formed by the superposition of two waves traveling in opposite directions. 
When two waves of the same frequency and amplitude travel in opposite directions in a medium, they interfere and form a standing wave.
The wavelength of the standing wave is determined by the properties of the medium. 
For a string, the wave speed depends on the tension and the mass per unit length. 
The fundamental frequency of a string is the lowest frequency at which a standing wave can be formed.

Transverse waves are waves in which the displacement of the medium is perpendicular to the direction of propagation of the wave. 
A wave on a string is a common example of a transverse wave. 
The speed of a transverse wave on a string is given by the square root of the tension divided by the linear mass density.
In a transverse wave, the particles of the medium move up and down as the wave travels from left to right.

Superposition is the principle that when two or more waves overlap in space, the resulting displacement is the sum of the individual displacements. 
This principle is fundamental to understanding interference, diffraction, and standing waves.
The frequency of the wave is the number of oscillations per unit time, while the period is the time taken for one complete oscillation.
The relationship between wave speed, frequency, and wavelength is given by v = fλ.
"""

def test_optimization():
    print("Extracting concepts and relationships from synthetic waves text...")
    concepts, relationships = extract_concepts(WAVES_TEXT, top_n=20)
    
    print("\nExtraction Complete.")

if __name__ == "__main__":
    test_optimization()
