#include "processor.h"
#include "cids.h"

#include "base/source/fstreamer.h"
#include "pluginterfaces/vst/ivstparameterchanges.h"

#include <cstring>

namespace CubaseAi {

AudioTapProcessor::AudioTapProcessor()
{
	setControllerClass(kAudioTapControllerUID);
}

AudioTapProcessor::~AudioTapProcessor()
{
	ring_.setActive(false);
	ring_.close();
}

Steinberg::tresult PLUGIN_API AudioTapProcessor::initialize(Steinberg::FUnknown* context)
{
	auto result = AudioEffect::initialize(context);
	if (result != Steinberg::kResultOk)
		return result;

	addAudioInput(STR16("Stereo In"), Steinberg::Vst::SpeakerArr::kStereo);
	addAudioOutput(STR16("Stereo Out"), Steinberg::Vst::SpeakerArr::kStereo);
	return Steinberg::kResultOk;
}

Steinberg::tresult PLUGIN_API AudioTapProcessor::setActive(Steinberg::TBool state)
{
	if (state)
	{
		if (!ring_.open())
			return Steinberg::kResultFalse;
		ring_.setSampleRate(static_cast<uint32_t>(processSetup.sampleRate));
		ring_.setActive(true);
	}
	else
	{
		ring_.setActive(false);
		ring_.close();
	}
	return AudioEffect::setActive(state);
}

Steinberg::tresult PLUGIN_API AudioTapProcessor::setupProcessing(Steinberg::Vst::ProcessSetup& newSetup)
{
	auto result = AudioEffect::setupProcessing(newSetup);
	if (ring_.valid())
		ring_.setSampleRate(static_cast<uint32_t>(newSetup.sampleRate));
	return result;
}

Steinberg::tresult PLUGIN_API AudioTapProcessor::canProcessSampleSize(Steinberg::int32 symbolicSampleSize)
{
	if (symbolicSampleSize == Steinberg::Vst::kSample32)
		return Steinberg::kResultTrue;
	return Steinberg::kResultFalse;
}

Steinberg::tresult PLUGIN_API AudioTapProcessor::setBusArrangements(
    Steinberg::Vst::SpeakerArrangement* inputs, Steinberg::int32 numIns,
    Steinberg::Vst::SpeakerArrangement* outputs, Steinberg::int32 numOuts)
{
	if (numIns == 1 && numOuts == 1 && inputs && outputs &&
	    inputs[0] == Steinberg::Vst::SpeakerArr::kStereo &&
	    outputs[0] == Steinberg::Vst::SpeakerArr::kStereo)
	{
		return AudioEffect::setBusArrangements(inputs, numIns, outputs, numOuts);
	}
	return Steinberg::kResultFalse;
}

Steinberg::tresult PLUGIN_API AudioTapProcessor::setState(Steinberg::IBStream* state)
{
	if (!state)
		return Steinberg::kResultFalse;

	Steinberg::IBStreamer streamer(state, kLittleEndian);
	Steinberg::int32 bypass = 0;
	if (!streamer.readInt32(bypass))
		return Steinberg::kResultFalse;
	bypass_ = bypass != 0;
	return Steinberg::kResultOk;
}

Steinberg::tresult PLUGIN_API AudioTapProcessor::getState(Steinberg::IBStream* state)
{
	if (!state)
		return Steinberg::kResultFalse;

	Steinberg::IBStreamer streamer(state, kLittleEndian);
	streamer.writeInt32(bypass_ ? 1 : 0);
	return Steinberg::kResultOk;
}

Steinberg::tresult PLUGIN_API AudioTapProcessor::process(Steinberg::Vst::ProcessData& data)
{
	if (data.inputParameterChanges)
	{
		const auto numParams = data.inputParameterChanges->getParameterCount();
		for (Steinberg::int32 i = 0; i < numParams; ++i)
		{
			auto* queue = data.inputParameterChanges->getParameterData(i);
			if (!queue)
				continue;
			Steinberg::Vst::ParamValue value = 0;
			Steinberg::int32 sampleOffset = 0;
			if (queue->getPoint(queue->getPointCount() - 1, sampleOffset, value) == Steinberg::kResultTrue)
			{
				if (queue->getParameterId() == kBypassId)
					bypass_ = value >= 0.5;
			}
		}
	}

	if (data.numInputs < 1 || data.numOutputs < 1)
		return Steinberg::kResultOk;

	auto& input = data.inputs[0];
	auto& output = data.outputs[0];
	const auto numSamples = data.numSamples;
	if (numSamples <= 0)
		return Steinberg::kResultOk;

	for (Steinberg::int32 ch = 0; ch < input.numChannels && ch < output.numChannels; ++ch)
	{
		if (output.channelBuffers32[ch] != input.channelBuffers32[ch])
		{
			std::memcpy(output.channelBuffers32[ch], input.channelBuffers32[ch],
			            static_cast<size_t>(numSamples) * sizeof(float));
		}
	}
	output.silenceFlags = input.silenceFlags;

	if (!bypass_ && ring_.valid())
	{
		if (input.numChannels >= 2 && input.channelBuffers32[0] && input.channelBuffers32[1])
		{
			ring_.writeInterleaved(input.channelBuffers32[0], input.channelBuffers32[1],
			                       static_cast<uint32_t>(numSamples));
		}
		else if (input.numChannels == 1 && input.channelBuffers32[0])
		{
			ring_.writeInterleaved(input.channelBuffers32[0], input.channelBuffers32[0],
			                       static_cast<uint32_t>(numSamples));
		}
	}

	return Steinberg::kResultOk;
}

} // namespace CubaseAi
