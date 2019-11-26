# Changelog

All notable changes to this project can be found here.
The format of this changelog is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

#### 2019/11/27 [1.1.2](https://github.com/UACoreFacilitiesIT/UA-Clarity-API)

Clarity Api now extends UA-Generic-Rest-API. Host URLs are no longer hard-coded. 1.1.1 had merge conflicts, so it was updated to 1.1.2.

#### 2019/11/15 [1.1.0](https://github.com/UACoreFacilitiesIT/UA-Clarity-API/commit/37ba54bee86aff7350a8330f3567f1fda8053fa8)

Added a feature to download files by artifact, fixed some get bugs.

##### Fixed

- Fixed bug in get where pages without a next page would sometimes throw an error.

##### Added

- If an empty list is passed to get, an empty list will be returned.
- Enabled files to get retrieved with either artifact uri's or file uri's.

#### 2019/10/19 [1.0.3](https://github.com/UACoreFacilitiesIT/UA-Clarity-API/commit/fa9fd2b9610c14133c056d4c02ca2fbb4076d6bd)

There were some critical errors with the brute-batch-get function, so those have been fixed.

##### Fixed

- Removed unused, breaking import that isn't used.
- Multi-threaded gets would only return the max_pool assigned to the code (dependent upon the machine running it) + 1 number of gets; now it will actually get everything passed in.
- Cleaned up some bugs and confusion about the brute-batch-get function, where the output was not making tags as we had assumed. Now, the root tag is a general \<brute-batch-get> tag.
- Tried to reduce false positive patching on endpoints: resources.

##### Added

- Added timeouts to every get.
- Added more useful get tests.

#### 2019/10/09 [1.0.2](https://github.com/UACoreFacilitiesIT/UA-Clarity-API/commit/10d253d7d0390afaccfbd9165839fb03e06ed1e6)

The cache_get function was generating errors when a change happened between gets; now, it threads the get requests to minimize runtime.

##### Fixed

- Calling the get method twice would return the wrong thing if something changed. Now it returns the up-to-date information.

#### 2019/10/03 [1.0.1](https://github.com/UACoreFacilitiesIT/UA-Clarity-API/commit/032e5cc8c745e20e388b7f89b28a516f7e3cdbe5)

The initial release had a few problems from transferring. This is now the first stable point of this repo.

##### Fixed

- Project build now properly includes some required .xml files.
- test file now tests the appropriate file.

#### 2019/10/03 [1.0.0](https://github.com/UACoreFacilitiesIT/UA-Clarity-API/commit/1ea00740cadcc5569988163f0db4e901bde9ab04)

This is the initial start point for a University of Arizona Illumina Clarity API.

- Moved repo from private repo to public.
