#version 440

layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(binding = 1) uniform sampler2D source;

layout(std140, binding = 0) uniform buf {
    mat4  qt_Matrix;
    float qt_Opacity;
    vec4  edgeColor;
    float threshold;
    float edgeStrength;
    float bgStrength;     // intensité teinte sur le fond (ex: 0.15)
    vec2  texelSize;
} ubuf;

float luma(vec4 c) {
    return dot(c.rgb, vec3(0.299, 0.587, 0.114));
}

// Sobel sur un offset donné (pour le super-sampling)
float sobel(vec2 uv, vec2 t) {
    float tl = luma(texture(source, uv + vec2(-t.x, -t.y)));
    float tc = luma(texture(source, uv + vec2( 0.0,  -t.y)));
    float tr = luma(texture(source, uv + vec2( t.x,  -t.y)));
    float ml = luma(texture(source, uv + vec2(-t.x,   0.0)));
    float mr = luma(texture(source, uv + vec2( t.x,   0.0)));
    float bl = luma(texture(source, uv + vec2(-t.x,   t.y)));
    float bc = luma(texture(source, uv + vec2( 0.0,   t.y)));
    float br = luma(texture(source, uv + vec2( t.x,   t.y)));

    float gx = -tl - 2.0*ml - bl + tr + 2.0*mr + br;
    float gy = -tl - 2.0*tc - tr + bl + 2.0*bc + br;
    return sqrt(gx*gx + gy*gy);
}

void main() {
    vec2 uv = qt_TexCoord0;
    vec2 t  = ubuf.texelSize;

    // Super-sampling 4x (sous-pixels décalés d'un demi-texel)
    // → lisse les contours en escalier
    float e = 0.0;
    e += sobel(uv + vec2(-0.25, -0.25) * t, t);
    e += sobel(uv + vec2( 0.25, -0.25) * t, t);
    e += sobel(uv + vec2(-0.25,  0.25) * t, t);
    e += sobel(uv + vec2( 0.25,  0.25) * t, t);
    e *= 0.25;

    // Contour lissé avec zone de transition plus large
    float edgeMask = smoothstep(ubuf.threshold - 0.05,
                                ubuf.threshold + 0.15, e);

    // Fond = inverse du contour, mais atténué
    float bgMask = (1.0 - edgeMask) * ubuf.bgStrength;

    vec4 original = texture(source, uv);

    // Teinte contours forte + teinte fond douce
    vec4 col = mix(original, ubuf.edgeColor, edgeMask * ubuf.edgeStrength);
    col      = mix(col,      ubuf.edgeColor, bgMask);

    fragColor = col * ubuf.qt_Opacity;
}