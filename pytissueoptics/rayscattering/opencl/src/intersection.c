
struct Intersection {
    int status;
    float distance;
};

typedef struct Intersection Intersection;

struct Ray {
    float4 origin;
    float4 direction;
    float length;
};

typedef struct Ray Ray;

struct GemsBoxIntersection {
    bool rayIsInside;
    bool exists;
    float3 position;
};

typedef struct GemsBoxIntersection GemsBoxIntersection;


GemsBoxIntersection _getSolidCandidate(Ray ray, float3 minCorner, float3 maxCorner) {
    GemsBoxIntersection intersection;
    intersection.rayIsInside = true;
    intersection.exists = false;

    int quadrant[3];
    float3 candidatePlanes;
    for (uint i = 0; i < 3; i++) {
        if (ray.origin[i] < minCorner[i]) {
            quadrant[i] = 0;
            candidatePlanes[i] = minCorner[i];
            intersection.rayIsInside = false;
        } else if (ray.origin[i] > maxCorner[i]) {
            quadrant[i] = 1;
            candidatePlanes[i] = maxCorner[i];
            intersection.rayIsInside = false;
        } else {
            quadrant[i] = 2;
        }
    }

    if (intersection.rayIsInside) {
        return intersection;
    }

    float3 maxT;
    for (uint i = 0; i < 3; i++) {
        if (quadrant[i] != 2 && ray.direction[i] != 0.0f) {
            maxT[i] = (candidatePlanes[i] - ray.origin[i]) / ray.direction[i];
        } else {
            maxT[i] = -1.0f;
        }
    }

    uint plane = 0;
    for (uint i = 1; i < 3; i++) {
        if (maxT[plane] < maxT[i]) {
            plane = i;
        }
    }

    if (maxT[plane] < 0.0f) {
        return intersection;
    }
    if (maxT[plane] > ray.length) {
        return intersection;
    }
    for (uint i = 0; i < 3; i++) {
        if (plane != i) {
            intersection.position[i] = ray.origin[i] + maxT[plane] * ray.direction[i];
            if (intersection.position[i] < minCorner[i] || intersection.position[i] > maxCorner[i]) {
                return intersection;
            }
        } else {
            intersection.position[i] = candidatePlanes[i];
        }
    }

    intersection.exists = true;
    return intersection;
}

void _findBBoxIntersectingSolids(Ray ray, uint nSolids,
        __global Solid *solids, __global SolidCandidate *solidCandidates, uint gid){

    for (uint i = 0; i < nSolids; i++) {
        uint boxGID = gid * nSolids + i;
        solidCandidates[boxGID].solidID = i;

        GemsBoxIntersection gemsIntersection = _getSolidCandidate(ray, solids[i].bbox_min, solids[i].bbox_max);
        printf("Intersection with Solid ID %d : (isInside=%d, exists=%d, position=(%f, %f, %f))\n",
                i, gemsIntersection.rayIsInside, gemsIntersection.exists, gemsIntersection.position.x, gemsIntersection.position.y, gemsIntersection.position.z);
        if (gemsIntersection.rayIsInside) {
            solidCandidates[boxGID].distance = 0;
        } else if (!gemsIntersection.exists) {
            solidCandidates[boxGID].distance = -1;
        } else {
            solidCandidates[boxGID].distance = length(gemsIntersection.position - ray.origin.xyz);
        }
    }
}

void _sortSolidCandidates(__global SolidCandidate *solidCandidates, uint gid, uint nSolids) {
    for (uint i = 0; i < nSolids; i++) {
        uint boxGID = gid * nSolids + i;
        for (uint j = i + 1; j < nSolids; j++) {
            uint boxGID2 = gid * nSolids + j;
            if (solidCandidates[boxGID].distance > solidCandidates[boxGID2].distance) {
                SolidCandidate tmp = solidCandidates[boxGID];
                solidCandidates[boxGID] = solidCandidates[boxGID2];
                solidCandidates[boxGID2] = tmp;
            }
        }
    }
}

Intersection _findClosestPolygonIntersection(Ray ray, uint solidID, __global Solid *solids) {
        Intersection intersection;
        intersection.status = 0;
        intersection.distance = -1;
//        for (uint i = 0; i < solids[solidID].nPolygons; i++) {
//            uint polygonID = solids[solidID].firstPolygon + i;
//            float4 normal = solids[polygonID].normal;
//            float4 point = solids[polygonID].point;
//            float distance = dot(point - ray.origin, normal) / dot(ray.direction, normal);
//            if (distance > 0 && (intersection.distance < 0 || distance < intersection.distance)) {
//                intersection.distance = distance;
//                intersection.status = 1;
//            }
//        }
        return intersection;
}

Intersection findIntersection(Ray ray, uint nSolids,
        __global Solid *solids, __global SolidCandidate *solidCandidates, uint gid) {
    _findBBoxIntersectingSolids(ray,
                                nSolids, solids, solidCandidates, gid);
    _sortSolidCandidates(solidCandidates, gid, nSolids);

    Intersection closestIntersection;
    closestIntersection.status = 0;

    float closestDistance = INFINITY;
    for (uint i = 0; i < nSolids; i++) {
        uint boxGID = gid * nSolids + i;
        if (solidCandidates[boxGID].distance == -1) {
            printf("Skipping Solid %d\n", solidCandidates[boxGID].solidID);
            continue;
        }
        bool contained = solidCandidates[boxGID].distance == 0;
        if (!contained && closestIntersection.status == 1) {
            break;
        }

        uint solidID = solidCandidates[boxGID].solidID;
        printf("Testing polygons of Solid %d\n", solidID);
        Intersection intersection = _findClosestPolygonIntersection(ray, solidID, solids);
        if (intersection.status == 1  && intersection.distance < closestDistance) {
            closestDistance = intersection.distance;
            closestIntersection = intersection;
        }
    }
//    return _composeIntersection(ray, closestIntersection);  // todo
    return closestIntersection;
}

// ----------------- TEST KERNELS -----------------

__kernel void findIntersections(uint nSolids, __global Ray *rays, __global Solid *solids,
        __global SolidCandidate *solidCandidates, __global Intersection *intersections) {
    uint gid = get_global_id(0);
    intersections[gid] = findIntersection(rays[gid], nSolids, solids, solidCandidates, gid);
}
