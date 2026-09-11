select
    community_area,
    community_area_name

from {{ ref('community_areas') }}
