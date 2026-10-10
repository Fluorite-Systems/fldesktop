VERT_SRC = """
#version 440 core
layout(location=0) in vec2 aPos;
layout(location=1) in vec2 aTex;
out vec2 vTexCoord;
void main() {
    gl_Position = vec4(aPos, 0.0, 1.0);
    vTexCoord = aTex;
}
"""

FRAG_KAWASE_DOWN_SRC = """
#version 440 core
in vec2 vTexCoord;
out vec4 fragColor;
uniform sampler2D uTexture;
uniform vec2 uSrcTexelSize;
uniform float uBlurScale;
void main() {
    vec2 hp = uSrcTexelSize * uBlurScale;
    vec3 s  = texture(uTexture, vTexCoord).rgb * 4.0;
    s += texture(uTexture, vTexCoord + vec2(-hp.x, -hp.y)).rgb;
    s += texture(uTexture, vTexCoord + vec2( hp.x, -hp.y)).rgb;
    s += texture(uTexture, vTexCoord + vec2(-hp.x,  hp.y)).rgb;
    s += texture(uTexture, vTexCoord + vec2( hp.x,  hp.y)).rgb;
    fragColor = vec4(s / 8.0, 1.0);
}
"""

FRAG_KAWASE_UP_SRC = """
#version 440 core
in vec2 vTexCoord;
out vec4 fragColor;
uniform sampler2D uTexture;
uniform vec2 uSrcTexelSize;
uniform float uBlurScale;
void main() {
    vec2 hp = uSrcTexelSize * uBlurScale;
    vec3 s  = texture(uTexture, vTexCoord + vec2(-hp.x * 2.0, 0.0)).rgb;
    s += texture(uTexture, vTexCoord + vec2(-hp.x,  hp.y)).rgb * 2.0;
    s += texture(uTexture, vTexCoord + vec2( 0.0,   hp.y * 2.0)).rgb;
    s += texture(uTexture, vTexCoord + vec2( hp.x,  hp.y)).rgb * 2.0;
    s += texture(uTexture, vTexCoord + vec2( hp.x * 2.0, 0.0)).rgb;
    s += texture(uTexture, vTexCoord + vec2( hp.x, -hp.y)).rgb * 2.0;
    s += texture(uTexture, vTexCoord + vec2( 0.0,  -hp.y * 2.0)).rgb;
    s += texture(uTexture, vTexCoord + vec2(-hp.x, -hp.y)).rgb * 2.0;
    fragColor = vec4(s / 12.0, 1.0);
}
"""

FRAG_COPY_SRC = """
#version 440 core
in vec2 vTexCoord;
out vec4 fragColor;
uniform sampler2D uTexture;
void main() { fragColor = texture(uTexture, vTexCoord); }
"""

FRAG_WINDOW_SRC = """
#version 440 core
in vec2 vTexCoord;
out vec4 fragColor;

uniform sampler2D uScene;
uniform sampler2D uBlurred;
uniform sampler2D uSurface;

uniform vec2  uResolution;
uniform vec2  uRectMin;
uniform vec2  uRectSize;
uniform vec2  uPadUV;

uniform vec2  uShadowOffsetPx;
uniform float uShadowSpreadPx;
uniform float uShadowAlpha;

uniform vec3  uTint;
uniform float uTintAmount;

uniform float uWaveStrength;
uniform float uWaveScale;
uniform float uWaveAngle;
uniform float uTime;
uniform float uGlass;
uniform float uDrawSurface;

uniform float uChroma;
uniform float uLens;
uniform float uNoise;

uniform float uRimStrength;
uniform float uSparkleStrength;
uniform float uEdgeOffset;
uniform float uEdgeSensitivity;
uniform float uEnableGlow;

float hash21(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

vec3 sample_side(int side, float offset) {
    vec3 acc = vec3(0.0);
    for (int i = 0; i < 3; i++) {
        float t = 0.2 + float(i) * 0.3;
        vec2 q;
        if (side == 0) q = vec2(uRectMin.x + t * uRectSize.x,
                                uRectMin.y - offset);
        else if (side == 1) q = vec2(uRectMin.x + t * uRectSize.x,
                                     uRectMin.y + uRectSize.y + offset);
        else if (side == 2) q = vec2(uRectMin.x - offset,
                                     uRectMin.y + t * uRectSize.y);
        else q = vec2(uRectMin.x + uRectSize.x + offset,
                      uRectMin.y + t * uRectSize.y);
        vec2 g = clamp(vec2(q.x, 1.0 - q.y),
                       vec2(0.001), vec2(0.999));
        acc += texture(uBlurred, g).rgb;
    }
    return acc * (1.0 / 3.0);
}

vec3 edge_glow(vec2 localUV) {
    vec3 glow = vec3(0.0);
    if (uEnableGlow < 0.5) return glow;
    vec3 L_t = sample_side(0, uEdgeOffset);
    vec3 L_b = sample_side(1, uEdgeOffset);
    vec3 L_l = sample_side(2, uEdgeOffset);
    vec3 L_r = sample_side(3, uEdgeOffset);
    float lum_t = max(0.0, dot(L_t, vec3(0.299,0.587,0.114)) - 0.15);
    float lum_b = max(0.0, dot(L_b, vec3(0.299,0.587,0.114)) - 0.15);
    float lum_l = max(0.0, dot(L_l, vec3(0.299,0.587,0.114)) - 0.15);
    float lum_r = max(0.0, dot(L_r, vec3(0.299,0.587,0.114)) - 0.15);
    lum_t = pow(lum_t * uEdgeSensitivity, 1.4);
    lum_b = pow(lum_b * uEdgeSensitivity, 1.4);
    lum_l = pow(lum_l * uEdgeSensitivity, 1.4);
    lum_r = pow(lum_r * uEdgeSensitivity, 1.4);
    vec3 c_t = L_t / (lum_t + 0.5);
    vec3 c_b = L_b / (lum_b + 0.5);
    vec3 c_l = L_l / (lum_l + 0.5);
    vec3 c_r = L_r / (lum_r + 0.5);
    float rimUV = min(min(localUV.x, 1.0 - localUV.x),
                      min(localUV.y, 1.0 - localUV.y));
    float pxPerUV = min(uRectSize.x, uRectSize.y) * uResolution.x;
    float rimPx = rimUV * pxPerUV;
    float rimCore = 1.0 - smoothstep(0.0, 1.5, rimPx);
    float rimSoft = 1.0 - smoothstep(0.0, 5.0, rimPx);
    rimCore = pow(rimCore, 1.2);
    float w_t = 1.0 - smoothstep(0.0, 0.35, localUV.y);
    float w_b = smoothstep(0.65, 1.0, localUV.y);
    float w_l = 1.0 - smoothstep(0.0, 0.35, localUV.x);
    float w_r = smoothstep(0.65, 1.0, localUV.x);
    vec3 rimColor = c_t * (lum_t * w_t) + c_b * (lum_b * w_b)
                  + c_l * (lum_l * w_l) + c_r * (lum_r * w_r);
    vec3 rimGlow = rimColor
                 * (rimCore + rimSoft * 0.15) * uRimStrength;
    float cs = 0.13;
    vec2 cUL = localUV;
    vec2 cUR = vec2(1.0 - localUV.x, localUV.y);
    vec2 cLL = vec2(localUV.x, 1.0 - localUV.y);
    vec2 cLR = vec2(1.0 - localUV.x, 1.0 - localUV.y);
    float gUL = exp(-pow(length(cUL)/cs, 2.0));
    float gUR = exp(-pow(length(cUR)/cs, 2.0));
    float gLL = exp(-pow(length(cLL)/cs, 2.0));
    float gLR = exp(-pow(length(cLR)/cs, 2.0));
    float sUL = max(lum_t, lum_l), sUR = max(lum_t, lum_r);
    float sLL = max(lum_b, lum_l), sLR = max(lum_b, lum_r);
    vec3 ccUL = (lum_t >= lum_l) ? c_t : c_l;
    vec3 ccUR = (lum_t >= lum_r) ? c_t : c_r;
    vec3 ccLL = (lum_b >= lum_l) ? c_b : c_l;
    vec3 ccLR = (lum_b >= lum_r) ? c_b : c_r;
    vec3 sparkle = (ccUL * (gUL*sUL) + ccUR * (gUR*sUR)
                  + ccLL * (gLL*sLL) + ccLR * (gLR*sLR))
                 * uSparkleStrength;
    return rimGlow + sparkle;
}

void main() {
    vec2 uvQt = (uRectMin - uPadUV)
              + vec2(vTexCoord.x, 1.0 - vTexCoord.y)
                * (uRectSize + 2.0 * uPadUV);

    vec2 half_ = uRectSize * 0.5;
    vec2 center = uRectMin + half_;

    vec2 p = abs(uvQt - center) - half_;
    vec2 q = max(p, 0.0);
    float distW = length(q) + min(max(p.x, p.y), 0.0);
    float aa = fwidth(distW);
    float windowMask = 1.0 - smoothstep(-aa, aa, distW);

    vec2 localUV = (uvQt - uRectMin) / uRectSize;
    vec2 fromCenter = (localUV - 0.5) * 2.0;
    float r_lens = length(fromCenter);

    vec2 posPx    = uvQt   * uResolution;
    vec2 centerPx = center * uResolution;
    vec2 halfPx   = half_  * uResolution;
    vec2 pS = abs(posPx - (centerPx + uShadowOffsetPx)) - halfPx;
    vec2 qS = max(pS, 0.0);
    float dS = max(length(qS) + min(max(pS.x, pS.y), 0.0), 0.0);
    float shadow = exp(-(dS * dS) / (uShadowSpreadPx * uShadowSpreadPx));
    float shadowVisible = shadow * uShadowAlpha * (1.0 - windowMask);

    vec2 sceneUV = vec2(uvQt.x, 1.0 - uvQt.y);
    vec3 shadowedScene = texture(uScene, sceneUV).rgb
                       * (1.0 - shadowVisible);

    vec2 surfUV = vec2(localUV.x, 1.0 - localUV.y);

    if (uGlass < 0.5) {
        // Premultiplied source-over.
        vec4 surf = texture(uSurface, surfUV);
        vec3 combined = surf.rgb + shadowedScene * (1.0 - surf.a);
        fragColor = vec4(mix(shadowedScene, combined, windowMask), 1.0);
        return;
    }

    float lensProfile = r_lens * r_lens;
    vec2 lensDir = fromCenter / max(r_lens, 1e-4);
    vec2 lensOffset = -lensDir * lensProfile * uLens;
    vec2 lensUV = sceneUV + vec2(lensOffset.x, -lensOffset.y);

    vec2 fromCenterPx = fromCenter * halfPx;
    vec2 chromaDir = normalize(fromCenterPx + vec2(1e-5));
    float refPx = min(uResolution.x, uResolution.y);
    float edgeFactor = smoothstep(0.4, 1.0, r_lens);
    vec2 chromaOff = chromaDir * (uChroma * refPx) / uResolution
                   * edgeFactor;

    vec3 blur;
    if (uChroma > 0.0001) {
        float r = texture(uBlurred,
            clamp(lensUV + chromaOff, vec2(0.001), vec2(0.999))).r;
        vec3 g  = texture(uBlurred,
            clamp(lensUV, vec2(0.001), vec2(0.999))).rgb;
        float b = texture(uBlurred,
            clamp(lensUV - chromaOff, vec2(0.001), vec2(0.999))).b;
        blur = vec3(r, g.g, b);
    } else {
        blur = texture(uBlurred,
            clamp(lensUV, vec2(0.001), vec2(0.999))).rgb;
    }

    vec3 tinted = mix(blur * 0.92, uTint, uTintAmount);

    vec2 globalPx = uvQt * uResolution;
    vec2 waveDir = vec2(cos(uWaveAngle), sin(uWaveAngle));
    float waveT = dot(globalPx, waveDir);
    float ph = uTime * 0.2;
    float waveFreq = uWaveScale * 6.2831853 / 400.0;
    float wave = (sin(waveT * waveFreq * 1.0 + ph)
                + sin(waveT * waveFreq * 1.3 + 1.0 + ph * 1.3)
                + sin(waveT * waveFreq * 1.7 + 2.0 + ph * 0.7)) / 3.0;
    wave = smoothstep(0.20, 0.80, wave * 0.5 + 0.5);
    tinted *= 1.0 + wave * uWaveStrength;

    if (uNoise > 0.0001) {
        vec2 pp = floor(uvQt * uResolution);
        tinted += (hash21(pp) - 0.5) * uNoise;
    }

    vec3 glow = edge_glow(localUV);

    vec3 glass;
    if (uDrawSurface >= 0.5) {
        // Premultiplied source-over of surface content onto glass.
        vec4 surf = texture(uSurface, surfUV);
        glass = surf.rgb + (tinted + glow) * (1.0 - surf.a);
    } else {
        glass = tinted + glow;
    }

    fragColor = vec4(mix(shadowedScene, glass, windowMask), 1.0);
}
"""