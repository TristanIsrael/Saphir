#version 440

layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(binding = 1) uniform sampler2D source;

layout(std140, binding = 0) uniform buf {
    mat4  qt_Matrix;
    float qt_Opacity;
} ubuf;

void main() {
    vec4 c = texture(source, qt_TexCoord0);
    fragColor = vec4(1.0 - c.rgb, c.a) * ubuf.qt_Opacity;
}