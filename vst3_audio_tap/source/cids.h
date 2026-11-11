#pragma once

#include "pluginterfaces/base/funknown.h"
#include "pluginterfaces/vst/vsttypes.h"

namespace CubaseAi {

// Generated for Cubase AI Advisor Audio Tap — do not reuse in other plugins
static const Steinberg::FUID kAudioTapProcessorUID(
    0xA1C0F7E2, 0x4B9D4E1A, 0x9C2D8F61, 0x73B0E5A4);
static const Steinberg::FUID kAudioTapControllerUID(
    0xB2D1E8F3, 0x5C0E4F2B, 0xAD3E9072, 0x84C1F6B5);

#define AudioTapVST3Category "Fx|Analysis"

} // namespace CubaseAi
