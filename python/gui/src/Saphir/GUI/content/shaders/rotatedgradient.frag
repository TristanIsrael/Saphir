// GLSL pour Qt Quick ShaderEffect
uniform lowp float qt_Opacity;
uniform sampler2D colorSource; // gradient
uniform sampler2D maskSource;  // shape
uniform float angle;           // angle du gradient

varying highp vec2 qt_MultiTexCoord0;

void main() {
    // Coordonnées centrées [-0.5, 0.5]
    vec2 uv = qt_MultiTexCoord0 - vec2(0.5);

    // Rotation du gradient
    float rad = angle * 3.14159265 / 180.0;
    vec2 dir = vec2(cos(rad), sin(rad));

    // Calcul de la position le long du gradient
    float gradPos = dot(uv, dir) + 0.5;
    gradPos = clamp(gradPos, 0.0, 1.0);

    // Dégradé linéaire bleu → rose
    vec3 gradientColor = mix(vec3(0.305, 0.8, 0.77), vec3(1.0, 0.42, 0.42), gradPos);

    // Masque provenant du Shape
    float maskAlpha = texture(maskSource, qt_MultiTexCoord0).a;

    // Couleur finale avec masque et opacité Qt
    gl_FragColor = vec4(gradientColor, maskAlpha * qt_Opacity);
}