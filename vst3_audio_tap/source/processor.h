#pragma once

#include "public.sdk/source/vst/vstaudioeffect.h"
#include "shared_memory_ring.h"

namespace CubaseAi {

enum : Steinberg::Vst::ParamID
{
	kBypassId = 0
};

class AudioTapProcessor : public Steinberg::Vst::AudioEffect
{
public:
	AudioTapProcessor();
	~AudioTapProcessor() override;

	static Steinberg::FUnknown* createInstance(void* /*context*/)
	{
		return (Steinberg::Vst::IAudioProcessor*)new AudioTapProcessor;
	}

	Steinberg::tresult PLUGIN_API initialize(Steinberg::FUnknown* context) override;
	Steinberg::tresult PLUGIN_API setActive(Steinberg::TBool state) override;
	Steinberg::tresult PLUGIN_API setupProcessing(Steinberg::Vst::ProcessSetup& newSetup) override;
	Steinberg::tresult PLUGIN_API canProcessSampleSize(Steinberg::int32 symbolicSampleSize) override;
	Steinberg::tresult PLUGIN_API setBusArrangements(
	    Steinberg::Vst::SpeakerArrangement* inputs, Steinberg::int32 numIns,
	    Steinberg::Vst::SpeakerArrangement* outputs, Steinberg::int32 numOuts) override;
	Steinberg::tresult PLUGIN_API process(Steinberg::Vst::ProcessData& data) override;
	Steinberg::tresult PLUGIN_API setState(Steinberg::IBStream* state) override;
	Steinberg::tresult PLUGIN_API getState(Steinberg::IBStream* state) override;

private:
	cubase_ai::SharedMemoryRing ring_;
	bool bypass_ = false;
};

} // namespace CubaseAi
