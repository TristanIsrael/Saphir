#version 440

layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec2 pixelStep;
    int radius;
    float deviation;
    float hue;
    float saturation;
    float lightness;
};
layout(binding = 1) uniform sampler2D src;

#define PI 3.1415926538

float gaussianWeight(vec2 coords)
{
    float x2 = pow(coords.x, 2.0);
    float y2 = pow(coords.y, 2.0);
    float deviation2 = pow(deviation, 2.0);

    return (1.0 / (2.0 * PI * deviation2)) * exp(-(x2 + y2) / (2.0 * deviation2));
}

float RGBtoL(vec3 color)
{
    float cmin = min(color.r, min(color.g, color.b));
    float cmax = max(color.r, max(color.g, color.b));
    float l = (cmin + cmax) / 2.0;
    return l;
}

float hueToIntensity(float v1, float v2, float h)
{
    h = fract(h);
    if (h < 1.0 / 6.0)
        return v1 + (v2 - v1) * 6.0 * h;
    else if (h < 1.0 / 2.0)
        return v2;
    else if (h < 2.0 / 3.0)
        return v1 + (v2 - v1) * 6.0 * (2.0 / 3.0 - h);

    return v1;
}

vec3 HSLtoRGB(vec3 color)
{
    float h = color.x;
    float l = color.z;
    float s = color.y;

    if (s < 1.0 / 256.0)
        return vec3(l, l, l);

    float v1;
    float v2;
    if (l < 0.5)
        v2 = l * (1.0 + s);
    else
        v2 = (l + s) - (s * l);

    v1 = 2.0 * l - v2;

    float d = 1.0 / 3.0;
    float r = hueToIntensity(v1, v2, h + d);
    float g = hueToIntensity(v1, v2, h);
    float b = hueToIntensity(v1, v2, h - d);
    return vec3(r, g, b);
}


void main(void)
{
    vec3 sum = vec3(0.0, 0.0, 0.0);
    float gaussianSum = 0.0;
    for (int x = -radius; x <= radius; ++x) {
        for (int y = -radius; y <= radius; ++y) {
            vec2 c = qt_TexCoord0 + vec2(x, y) * pixelStep;
            float w = gaussianWeight(vec2(x, y));
            sum += texture(src, c).rgb * w;
            gaussianSum += w;
        }
    }

    float light = RGBtoL(sum / gaussianSum);
    float c = step(0.0, lightness);
    vec3 color = HSLtoRGB(vec3(hue, saturation, mix(light, c, abs(lightness))));
    fragColor = vec4(color, 1.0) * qt_Opacity;
}