-- Seed for arXiv_holidays.
--
-- Source: arxiv-lib.git/lib/arXiv/Config/Holidays.pm (@HOLIDAYS array,
-- lines 38-95 as of 2026-05). One row per ISO date. The `description`
-- column carries the inline perl comment verbatim.
--
-- After loading this seed, ops must keep the perl @HOLIDAYS array and
-- this table in sync (dual-write) until the perl side migrates onto
-- the DB.
--
-- Seeding for `created_by` is set to tapir_user.user_id = 48811 which is "arXiv Admin"

INSERT INTO `arXiv_holidays` (`freeze_skip_date`, `description`, `created_by`) VALUES
  -- Pre-2020 entries: removed from the perl @HOLIDAYS array in
  -- arxiv-lib commit 1f5b17cd (2026-01-08 "hotfix for holiday schedule
  -- of 2026"). Preserved here as the DB historical record.
  ('2003-12-25', '2003 thu', '48811'),
  ('2003-12-26', '2003 fri', '48811'),
  ('2004-01-01', '2004 new year thu', '48811'),
  ('2004-01-02', '2004 new year fri', '48811'),

  ('2004-11-25', '2004 thanksgiving thu', '48811'),
  ('2004-12-24', '2004 fri', '48811'),
  ('2004-12-28', '2004 tue', '48811'),
  ('2004-12-30', '2004 thu', '48811'),

  ('2005-11-24', '2005 thanksgiving thu', '48811'),
  ('2005-12-27', '2005 tue', '48811'),
  ('2005-12-29', '2005 thu', '48811'),

  ('2006-11-23', '2006 thanksgiving thu', '48811'),
  ('2006-12-25', '2006 mon', '48811'),
  ('2006-12-26', '2006 tue', '48811'),
  ('2007-01-01', '2007 new year mon', '48811'),

  ('2007-11-22', '2007 thanksgiving thu', '48811'),
  ('2007-12-24', '2007 mon', '48811'),
  ('2007-12-25', '2007 tue', '48811'),
  ('2007-12-31', '2007 new year mon', '48811'),
  ('2008-01-01', '2008 new year tue', '48811'),

  ('2008-07-04', '2008 July 4th', '48811'),
  ('2008-11-27', '2008 thanksgiving thu', '48811'),
  ('2008-12-25', '2008 thu', '48811'),
  ('2008-12-26', '2008 fri', '48811'),
  ('2008-12-29', '2008 mon', '48811'),
  ('2008-12-31', '2008 new year wed', '48811'),
  ('2009-01-01', '2009 new year thu', '48811'),

  ('2009-07-08', '2009 data recovery after bad rsync', '48811'),
  ('2009-11-26', '2009 thanksgiving thu', '48811'),
  ('2009-12-25', '2009 fri', '48811'),
  ('2009-12-28', '2009 mon', '48811'),
  ('2009-12-29', '2009 tue', '48811'),
  ('2009-12-31', '2009 new year thu', '48811'),
  ('2010-01-01', '2010 new year fri', '48811'),

  ('2010-11-25', '2010 thanksgiving thu', '48811'),
  ('2010-12-27', '2010 mon', '48811'),
  ('2010-12-28', '2010 tue', '48811'),
  ('2010-12-30', '2010 thu', '48811'),
  ('2010-12-31', '2010 fri before new year sat', '48811'),

  ('2011-11-24', '2011 thanksgiving thu', '48811'),
  ('2011-12-26', '2011 mon', '48811'),
  ('2011-12-27', '2011 tue', '48811'),
  ('2011-12-28', '2011 wed', '48811'),
  ('2011-12-30', '2011 fri before new year', '48811'),
  ('2012-01-02', '2012 mon after new year', '48811'),

  ('2012-11-22', '2012 thanksgiving thu', '48811'),
  ('2012-12-24', '2012 mon', '48811'),
  ('2012-12-25', '2012 tue', '48811'),
  ('2012-12-27', '2012 thu', '48811'),
  ('2012-12-28', '2012 fri before new year', '48811'),
  ('2013-01-01', '2013 new year tue', '48811'),

  ('2013-11-28', '2013 Thanksgiving thu', '48811'),
  ('2013-12-25', '2013 winter holiday break wed', '48811'),
  ('2013-12-26', '2013 winter holiday break thu', '48811'),
  ('2013-12-31', '2013 tue', '48811'),
  ('2014-01-01', '2014 new year wed', '48811'),

  ('2014-11-27', '2014 Thanksgiving thu', '48811'),
  ('2014-12-25', '2014 winter holiday break thu', '48811'),
  ('2014-12-26', '2014 winter holiday break fri', '48811'),
  ('2014-12-31', '2014 wed', '48811'),
  ('2015-01-01', '2015 new year thu', '48811'),

  ('2015-11-26', '2015 Thanksgiving thu', '48811'),
  ('2015-12-25', '2015 winter holiday break fri', '48811'),
  ('2015-12-29', '2015 winter holiday break tue', '48811'),
  ('2016-01-01', '2016 new year fri', '48811'),

  ('2016-11-24', '2016 Thanksgiving', '48811'),
  ('2016-12-26', '2016 Winter Holiday', '48811'),
  ('2016-12-28', '2016 Winter Holiday', '48811'),

  ('2017-03-14', '/data/new/upload glitch', '48811'),
  ('2017-11-13', 'CIT outage/unscheduled reboots', '48811'),
  ('2017-11-23', '2017 Thanksgiving', '48811'),
  ('2017-12-25', '2017 winter holiday break mon', '48811'),
  ('2017-12-27', '2017 winter holiday break wed', '48811'),
  ('2018-01-01', '2018 new year mon', '48811'),

  ('2018-03-26', 'CIT outage', '48811'),
  ('2018-09-03', '2018 Labor Day', '48811'),
  ('2018-11-22', '2018 Thanksgiving', '48811'),
  ('2018-12-24', '2018 winter holiday break mon', '48811'),
  ('2018-12-25', '2018 winter holiday break tue', '48811'),
  ('2018-12-27', '2018 winter holiday break thu', '48811'),
  ('2019-01-01', '2019 new year tue', '48811'),

  ('2019-01-21', '2019 MLK mon', '48811'),
  ('2019-09-02', '2019 Labor Day', '48811'),
  ('2019-11-07', 'CIT outage', '48811'),
  ('2019-11-28', '2019 Thanksgiving', '48811'),
  ('2019-12-25', '2019 winter holiday break wed', '48811'),
  ('2019-12-26', '2019 winter holiday break thu', '48811'),
  ('2019-12-30', '2019 winter holiday break mon', '48811'),

  ('2020-01-01', '2020 new year wed', '48811'),
  ('2020-01-20', '2020 MLK mon', '48811'),
  ('2020-06-09', '2020 strike tue', '48811'),
  ('2020-11-26', '2020 Thanksgiving', '48811'),
  ('2020-12-25', '2020 winter holiday break fri', '48811'),
  ('2020-12-29', '2020 winter holiday break tue', '48811'),
  ('2020-12-30', '2020 winter holiday break wed', '48811'),

  ('2021-01-01', '2021 new year fri', '48811'),
  ('2021-10-20', '2021 October staff meeting wed', '48811'),
  ('2021-11-25', '2021 Thanksgiving', '48811'),
  ('2021-12-24', '2021 winter holiday break fri', '48811'),
  ('2021-12-28', '2021 winter holiday break tue', '48811'),
  ('2021-12-30', '2021 winter holiday break thu', '48811'),

  ('2022-01-17', '2022 MLK', '48811'),
  ('2022-06-20', '2022 Juneteenth', '48811'),
  ('2022-09-05', '2022 Labor Day', '48811'),
  ('2022-11-24', '2022 Thanksgiving', '48811'),
  ('2022-12-27', '2022 Winter holiday tue', '48811'),
  ('2022-12-29', '2022 Winter holiday thu', '48811'),

  ('2023-01-16', '2023 MLK', '48811'),
  ('2023-06-14', '2023 Admin retreat', '48811'),
  ('2023-06-19', '2023 Juneteenth', '48811'),
  ('2023-07-04', '2023 4th', '48811'),
  ('2023-08-17', '2023 arXiv strategy meeting with IOI', '48811'),
  ('2023-09-04', '2023 Labor Day', '48811'),
  ('2023-11-23', '2023 Thanksgiving', '48811'),
  ('2023-12-25', '2023 Winter break', '48811'),
  ('2023-12-27', '2023 Winter break', '48811'),

  ('2024-01-15', '2024 MLK', '48811'),
  ('2024-05-22', '2024 Admin retreat', '48811'),
  ('2024-06-19', '2024 Juneteenth', '48811'),
  ('2024-07-04', '2024 4th', '48811'),
  ('2024-09-02', '2024 Labor Day', '48811'),
  ('2024-10-08', '2024 All-staff NYC Retreat', '48811'),
  ('2024-11-28', '2024 Thanksgiving', '48811'),
  ('2024-12-25', '2024 Winter Holidays', '48811'),
  ('2024-12-26', '2024 Winter Holidays', '48811'),
  ('2024-12-31', '2024 Winter Holidays', '48811'),

  ('2025-01-01', '2025 New Years Day', '48811'),
  ('2025-01-20', '2025 MLK', '48811'),
  ('2025-06-19', '2025 Juneteenth', '48811'),
  ('2025-07-04', '2025 USA Independence Day', '48811'),
  ('2025-07-06', '2025 USA Independence Day observed', '48811'),
  ('2025-09-01', '2025 USA Labor day', '48811'),
  ('2025-11-27', '2025 USA Thanksgiving', '48811'),
  ('2025-12-25', '2025 Christmas Day', '48811'),
  ('2025-12-30', '2025 arXiv Holiday', '48811'),

  ('2026-01-01', '2026 New Year''s Day', '48811'),
  ('2026-01-19', '2026 MLK', '48811'),
  ('2026-06-19', '2026 Juneteenth', '48811'),
  ('2026-07-03', '2026 July 4th', '48811'),
  ('2026-09-07', '2026 Labor day', '48811'),
  ('2026-11-26', '2026 Thanksgiving', '48811'),
  ('2026-12-25', '2026 Friday of winter break', '48811'),
  ('2026-12-29', '2026 Tuesday of winter break', '48811'),
  ('2026-12-31', '2026 Thursday of winter break', '48811');
