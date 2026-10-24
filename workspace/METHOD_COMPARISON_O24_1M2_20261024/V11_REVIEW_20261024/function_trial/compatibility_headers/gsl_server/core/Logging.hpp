#pragma once
#define GSL_ERROR(...) throw std::runtime_error("visibility capacity error")
#define GSL_ASSERT(x) assert(x)
