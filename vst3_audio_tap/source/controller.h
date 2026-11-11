#pragma once

#include "public.sdk/source/vst/vsteditcontroller.h"

namespace CubaseAi {

class AudioTapController : public Steinberg::Vst::EditControllerEx1
{
public:
	static Steinberg::FUnknown* createInstance(void* /*context*/)
	{
		return (Steinberg::Vst::IEditController*)new AudioTapController;
	}

	Steinberg::tresult PLUGIN_API initialize(Steinberg::FUnknown* context) override;
	Steinberg::tresult PLUGIN_API setComponentState(Steinberg::IBStream* state) override;
};

} // namespace CubaseAi
