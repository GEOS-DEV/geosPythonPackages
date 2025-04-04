# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
class GeosTrameException( Exception ):
    pass


class FileExistsException( GeosTrameException ):
    pass


class BadExecutableException( GeosTrameException ):
    pass
