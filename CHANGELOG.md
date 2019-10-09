# Changelog

All notable changes to this project can be found here.
The format of this changelog is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

#### 2019/10/09 [1.0.2](https://github.com/UACoreFacilitiesIT/UA-Clarity-API)
The cache_get function was generating errors when a change happened between gets; now, it threads the get requests to minimize runtime.

###### Fixed
- Calling the get method twice would return the wrong thing if something changed. Now it returns the up-to-date information.

#### 2019/10/03 [1.0.1](https://github.com/UACoreFacilitiesIT/UA-Clarity-API/commit/032e5cc8c745e20e388b7f89b28a516f7e3cdbe5)
The initial release had a few problems from transferring. This is now the first stable point of this repo.

###### Fixed

- Project build now properly includes some required .xml files.
- test file now tests the appropriate file.

#### 2019/10/03 [1.0.0](https://github.com/UACoreFacilitiesIT/UA-Clarity-API/commit/1ea00740cadcc5569988163f0db4e901bde9ab04)
This is the initial start point for a University of Arizona Illumina Clarity API.

- Moved repo from private repo to public.
