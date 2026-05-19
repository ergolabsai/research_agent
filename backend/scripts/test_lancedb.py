# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""
Quick test script for LanceDB search (delegates to shared utility).
"""
from advisor_pipeline.utils.lancedb_search import vector_search, fts_search


if __name__ == "__main__":
    # Test with a conceptual query
    vector_search(
        "Here we present a three-wavelength, nanosecond-pulsed laser diagnostic for the joint retrieval of temperature and particle-size distributions in WEE. To address the coupling challenge in extinction measurements within plasma-particle multiphase flows, a spectral-ratio decoupling model is developed to transform the inverse problem into a deterministic, closed-form solution, effectively isolating the temperature-dependent absorption alpha(T) from the size-dependent scattering beta(D). Furthermore, we implement a structured index-driven inversion (SID-Inv) strategy, which accelerates the inversion by four orders of magnitude compared to iterative methods. Our diagnostic platform captured tri-wavelength images covering the complete WEE evolution, which lasts only tens of microseconds. The reconstructed fields resolve the coupled evolution of plasma temperature and particle growth and coalescence, revealing a cooling-condensation pathway: the peak temperature decreased from 5742 K at 5.5 mus to 5133 K at 10 mus, while the characteristic particle diameter increased from 121.5 to 130.5 nm. This framework enables pixel-wise, synchronous retrieval in WEE and is applicable to other non-isothermal plasma-particle events.", 
        limit=5)