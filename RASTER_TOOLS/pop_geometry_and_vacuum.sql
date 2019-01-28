\echo Populating geometry columns...
select clock_timestamp();
select populate_geometry_columns();

\echo Vacuuming...
select clock_timestamp();
vacuum;

\echo Vacuuming full...
select clock_timestamp();
vacuum full;

select clock_timestamp();
