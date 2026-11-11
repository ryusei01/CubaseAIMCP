#pragma once

#include <cstdint>
#include <cstring>

#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

namespace cubase_ai {

constexpr uint32_t kTapMagic = 0x54414243u; // 'CBAT'
constexpr uint32_t kTapVersion = 1u;
constexpr uint32_t kTapChannels = 2u;
constexpr uint32_t kDefaultCapacityFrames = 48000u * 30u;
constexpr wchar_t kSharedMemoryName[] = L"CubaseAiAdvisorTap";

#pragma pack(push, 1)
struct TapHeader
{
	uint32_t magic;
	uint32_t version;
	uint32_t sampleRate;
	uint32_t channels;
	uint32_t capacityFrames;
	uint32_t bytesPerFrame;
	uint64_t writeIndex;
	uint32_t active;
	uint32_t reserved;
};
#pragma pack(pop)

static_assert(sizeof(TapHeader) == 40, "TapHeader must be 40 bytes");

inline size_t tapTotalBytes(uint32_t capacityFrames)
{
	return sizeof(TapHeader) + static_cast<size_t>(capacityFrames) * kTapChannels * sizeof(float);
}

class SharedMemoryRing
{
public:
	SharedMemoryRing() = default;
	~SharedMemoryRing() { close(); }

	SharedMemoryRing(const SharedMemoryRing&) = delete;
	SharedMemoryRing& operator=(const SharedMemoryRing&) = delete;

	bool open(uint32_t capacityFrames = kDefaultCapacityFrames)
	{
		close();
		capacityFrames_ = capacityFrames;
		const SIZE_T bytes = static_cast<SIZE_T>(tapTotalBytes(capacityFrames_));

		mapping_ = CreateFileMappingW(INVALID_HANDLE_VALUE, nullptr, PAGE_READWRITE, 0,
		                              static_cast<DWORD>(bytes), kSharedMemoryName);
		if (!mapping_)
			return false;

		view_ = static_cast<uint8_t*>(MapViewOfFile(mapping_, FILE_MAP_ALL_ACCESS, 0, 0, bytes));
		if (!view_)
		{
			CloseHandle(mapping_);
			mapping_ = nullptr;
			return false;
		}

		header_ = reinterpret_cast<TapHeader*>(view_);
		samples_ = reinterpret_cast<float*>(view_ + sizeof(TapHeader));

		if (header_->magic != kTapMagic)
		{
			std::memset(view_, 0, bytes);
			header_->magic = kTapMagic;
			header_->version = kTapVersion;
			header_->sampleRate = 48000;
			header_->channels = kTapChannels;
			header_->capacityFrames = capacityFrames_;
			header_->bytesPerFrame = kTapChannels * sizeof(float);
			header_->writeIndex = 0;
			header_->active = 0;
			header_->reserved = 0;
		}
		return true;
	}

	void close()
	{
		if (view_)
		{
			UnmapViewOfFile(view_);
			view_ = nullptr;
		}
		if (mapping_)
		{
			CloseHandle(mapping_);
			mapping_ = nullptr;
		}
		header_ = nullptr;
		samples_ = nullptr;
	}

	void setSampleRate(uint32_t sampleRate)
	{
		if (header_)
			header_->sampleRate = sampleRate;
	}

	void setActive(bool active)
	{
		if (header_)
			header_->active = active ? 1u : 0u;
	}

	void writeInterleaved(const float* left, const float* right, uint32_t numFrames)
	{
		if (!header_ || !samples_ || numFrames == 0)
			return;

		const uint32_t capacity = header_->capacityFrames;
		uint64_t writeIndex = header_->writeIndex;

		for (uint32_t i = 0; i < numFrames; ++i)
		{
			const uint32_t pos = static_cast<uint32_t>(writeIndex % capacity);
			const uint32_t base = pos * kTapChannels;
			samples_[base + 0] = left ? left[i] : 0.f;
			samples_[base + 1] = right ? right[i] : 0.f;
			++writeIndex;
		}

		InterlockedExchange64(reinterpret_cast<volatile LONG64*>(&header_->writeIndex),
		                      static_cast<LONG64>(writeIndex));
	}

	bool valid() const { return header_ != nullptr; }

private:
	HANDLE mapping_ = nullptr;
	uint8_t* view_ = nullptr;
	TapHeader* header_ = nullptr;
	float* samples_ = nullptr;
	uint32_t capacityFrames_ = kDefaultCapacityFrames;
};

} // namespace cubase_ai
