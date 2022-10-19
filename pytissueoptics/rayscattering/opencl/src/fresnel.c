
struct FresnelIntersection {
    float3 incidencePlane;
    uint isReflected;
    float angleDeflection;
    uint nextMaterialID;
};

typedef struct FresnelIntersection FresnelIntersection;


float _getReflectionCoefficient(float n1, float n2, float thetaIn) {
    if (n1 == n2) {
        return 0;
    }
    if (thetaIn == 0) {
        float R = (n2 - n1) / (n2 - n1);
        return R * R;
    }

    float sa1 = sin(thetaIn);

    float sa2 = sa1 * n1 / n2;
    if (sa2 > 1) {
        return 1;
    }

    float ca1 = sqrt(1 - sa1 * sa1);
    float ca2 = sqrt(1 - sa2 * sa2);

    float cap = ca1 * ca2 - sa1 * sa2;
    float cam = ca1 * ca2 + sa1 * sa2;
    float sap = sa1 * ca2 + ca1 * sa2;
    float sam = sa1 * ca2 - ca1 * sa2;

    return 0.5 * sam * sam * (cap * cap + cam * cam) / (sap * sap * cam * cam);
}

bool _getIsReflected(float nIn, float nOut, float thetaIn) {
    float R = _getReflectionCoefficient(nIn, nOut, thetaIn);
    if (R > 0.5) {  // fixme: we need to get a random number over here
        return true;
    }
    return false;
}

float _getReflectionDeflection(float thetaIn) {
    return 2 * thetaIn - M_PI_F;
}

float _getRefractionDeflection(float nIn, float nOut, float thetaIn) {
    float sinThetaOut = nIn / nOut * sin(thetaIn);
    float thetaOut = asin(sinThetaOut);
    return thetaIn - thetaOut;
}

void _createFresnelIntersection(FresnelIntersection* fresnelIntersection,
                                float nIn, float nOut, float thetaIn) {
    fresnelIntersection->isReflected = _getIsReflected(nIn, nOut, thetaIn);

    if (fresnelIntersection->isReflected) {
        fresnelIntersection->angleDeflection = _getReflectionDeflection(thetaIn);
    } else {
        fresnelIntersection->angleDeflection = _getRefractionDeflection(nIn, nOut, thetaIn);
    }
}

FresnelIntersection computeFresnelIntersection(float3 rayDirection, Intersection *intersection,
        __constant Material *materials, __global Surface *surfaces) {
    FresnelIntersection fresnelIntersection;
    float3 normal = intersection->normal;

    float nIn;
    float nOut;

    bool goingInside = dot(rayDirection, normal) < 0;
    if (goingInside) {
        normal *= -1;
        nIn = materials[surfaces[intersection->surfaceID].outsideMaterialID].n;
        nOut = materials[surfaces[intersection->surfaceID].insideMaterialID].n;
        fresnelIntersection.nextMaterialID = surfaces[intersection->surfaceID].insideMaterialID;
    } else {
        nIn = materials[surfaces[intersection->surfaceID].insideMaterialID].n;
        nOut = materials[surfaces[intersection->surfaceID].outsideMaterialID].n;
        fresnelIntersection.nextMaterialID = surfaces[intersection->surfaceID].outsideMaterialID;
    }

    fresnelIntersection.incidencePlane = cross(rayDirection, normal);
    if (length(fresnelIntersection.incidencePlane) < 0.0000001f) {
        fresnelIntersection.incidencePlane = getAnyOrthogonal(&rayDirection);
    }
    fresnelIntersection.incidencePlane = normalize(fresnelIntersection.incidencePlane);

    float thetaIn = acos(dot(normal, rayDirection));

    _createFresnelIntersection(&fresnelIntersection, nIn, nOut, thetaIn);

    return fresnelIntersection;
}