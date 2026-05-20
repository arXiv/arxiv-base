-- Seed for arXiv_publish_holidays.
--
-- Source: arxiv-lib.git/lib/arXiv/Config/Holidays.pm (@HOLIDAYS array,
-- lines 38-95 as of 2026-05). One row per ISO date. The `description`
-- column carries the inline perl comment verbatim.
--
-- After loading this seed, ops must keep the perl @HOLIDAYS array and
-- this table in sync (dual-write) until the perl side migrates onto
-- the DB. See the operational rule in publish.git CLAUDE.md.

INSERT INTO `arXiv_publish_holidays` (`holiday_date`, `description`, `created_by`) VALUES
  ('2020-01-01', '2020 new year wed', 'seed'),
  ('2020-01-20', '2020 MLK mon', 'seed'),
  ('2020-06-09', '2020 strike tue', 'seed'),
  ('2020-11-26', '2020 Thanksgiving', 'seed'),
  ('2020-12-25', '2020 winter holiday break fri', 'seed'),
  ('2020-12-29', '2020 winter holiday break tue', 'seed'),
  ('2020-12-30', '2020 winter holiday break wed', 'seed'),

  ('2021-01-01', '2021 new year fri', 'seed'),
  ('2021-10-20', '2021 October staff meeting wed', 'seed'),
  ('2021-11-25', '2021 Thanksgiving', 'seed'),
  ('2021-12-24', '2021 winter holiday break fri', 'seed'),
  ('2021-12-28', '2021 winter holiday break tue', 'seed'),
  ('2021-12-30', '2021 winter holiday break thu', 'seed'),

  ('2022-01-17', '2022 MLK', 'seed'),
  ('2022-06-20', '2022 Juneteenth', 'seed'),
  ('2022-09-05', '2022 Labor Day', 'seed'),
  ('2022-11-24', '2022 Thanksgiving', 'seed'),
  ('2022-12-27', '2022 Winter holiday tue', 'seed'),
  ('2022-12-29', '2022 Winter holiday thu', 'seed'),

  ('2023-01-16', '2023 MLK', 'seed'),
  ('2023-06-14', '2023 Admin retreat', 'seed'),
  ('2023-06-19', '2023 Juneteenth', 'seed'),
  ('2023-07-04', '2023 4th', 'seed'),
  ('2023-08-17', '2023 arXiv strategy meeting with IOI', 'seed'),
  ('2023-09-04', '2023 Labor Day', 'seed'),
  ('2023-11-23', '2023 Thanksgiving', 'seed'),
  ('2023-12-25', '2023 Winter break', 'seed'),
  ('2023-12-27', '2023 Winter break', 'seed'),

  ('2024-01-15', '2024 MLK', 'seed'),
  ('2024-05-22', '2024 Admin retreat', 'seed'),
  ('2024-06-19', '2024 Juneteenth', 'seed'),
  ('2024-07-04', '2024 4th', 'seed'),
  ('2024-09-02', '2024 Labor Day', 'seed'),
  ('2024-10-08', '2024 All-staff NYC Retreat', 'seed'),
  ('2024-11-28', '2024 Thanksgiving', 'seed'),
  ('2024-12-25', '2024 Winter Holidays', 'seed'),
  ('2024-12-26', '2024 Winter Holidays', 'seed'),
  ('2024-12-31', '2024 Winter Holidays', 'seed'),

  ('2025-01-01', '2025 New Years Day', 'seed'),
  ('2025-01-20', '2025 MLK', 'seed'),
  ('2025-06-19', '2025 Juneteenth', 'seed'),
  ('2025-07-04', '2025 USA Independence Day', 'seed'),
  ('2025-07-06', '2025 USA Independence Day observed', 'seed'),
  ('2025-09-01', '2025 USA Labor day', 'seed'),
  ('2025-11-27', '2025 USA Thanksgiving', 'seed'),
  ('2025-12-25', '2025 Christmas Day', 'seed'),
  ('2025-12-30', '2025 arXiv Holiday', 'seed'),

  ('2026-01-01', '2026 New Year''s Day', 'seed'),
  ('2026-01-19', '2026 MLK', 'seed'),
  ('2026-06-19', '2026 Juneteenth', 'seed'),
  ('2026-07-03', '2026 July 4th', 'seed'),
  ('2026-09-07', '2026 Labor day', 'seed'),
  ('2026-11-26', '2026 Thanksgiving', 'seed'),
  ('2026-12-25', '2026 Friday of winter break', 'seed'),
  ('2026-12-29', '2026 Tuesday of winter break', 'seed'),
  ('2026-12-31', '2026 Thursday of winter break', 'seed');
