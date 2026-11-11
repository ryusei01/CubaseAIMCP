#include "processor.h"
#include "controller.h"
#include "cids.h"
#include "version.h"

#include "public.sdk/source/main/pluginfactory.h"

#define stringPluginName "Cubase AI Audio Tap"

using namespace Steinberg::Vst;
using namespace CubaseAi;

BEGIN_FACTORY_DEF("Cubase AI Advisor",
                  "https://localhost",
                  "mailto:local@localhost")

	DEF_CLASS2(INLINE_UID_FROM_FUID(kAudioTapProcessorUID),
	           PClassInfo::kManyInstances,
	           kVstAudioEffectClass,
	           stringPluginName,
	           Vst::kDistributable,
	           AudioTapVST3Category,
	           FULL_VERSION_STR,
	           kVstVersionString,
	           AudioTapProcessor::createInstance)

	DEF_CLASS2(INLINE_UID_FROM_FUID(kAudioTapControllerUID),
	           PClassInfo::kManyInstances,
	           kVstComponentControllerClass,
	           stringPluginName "Controller",
	           0,
	           "",
	           FULL_VERSION_STR,
	           kVstVersionString,
	           AudioTapController::createInstance)

END_FACTORY
