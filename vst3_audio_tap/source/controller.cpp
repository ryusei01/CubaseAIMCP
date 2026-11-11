#include "controller.h"
#include "processor.h"

#include "base/source/fstreamer.h"

namespace CubaseAi {

Steinberg::tresult PLUGIN_API AudioTapController::initialize(Steinberg::FUnknown* context)
{
	auto result = EditControllerEx1::initialize(context);
	if (result != Steinberg::kResultOk)
		return result;

	parameters.addParameter(
	    STR16("Bypass"), nullptr, 1, 0,
	    Steinberg::Vst::ParameterInfo::kCanAutomate | Steinberg::Vst::ParameterInfo::kIsBypass,
	    kBypassId);
	return result;
}

Steinberg::tresult PLUGIN_API AudioTapController::setComponentState(Steinberg::IBStream* state)
{
	if (!state)
		return Steinberg::kResultFalse;

	Steinberg::IBStreamer streamer(state, kLittleEndian);
	Steinberg::int32 bypass = 0;
	if (!streamer.readInt32(bypass))
		return Steinberg::kResultFalse;

	setParamNormalized(kBypassId, bypass ? 1.0 : 0.0);
	return Steinberg::kResultOk;
}

} // namespace CubaseAi
