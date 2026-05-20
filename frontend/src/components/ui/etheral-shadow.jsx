'use client';

import React, { useRef, useId, useEffect } from 'react';
import { animate, useMotionValue } from 'framer-motion';

function mapRange(value, fromLow, fromHigh, toLow, toHigh) {
    if (fromLow === fromHigh) {
        return toLow;
    }
    const percentage = (value - fromLow) / (fromHigh - fromLow);
    return toLow + percentage * (toHigh - toLow);
}

const useInstanceId = () => {
    const id = useId();
    const cleanId = id.replace(/:/g, "");
    const instanceId = `shadowoverlay-${cleanId}`;
    return instanceId;
};

export function EtheralShadow({
    sizing = 'fill',
    color = 'rgba(43, 205, 255, 1)',
    animation,
    noise,
    style,
    className
}) {
    const id = useInstanceId();
    const animationEnabled = animation && animation.scale > 0;
    const feColorMatrixRef = useRef(null);
    const hueRotateMotionValue = useMotionValue(180);
    const hueRotateAnimation = useRef(null);

    const displacementScale = animation ? mapRange(animation.scale, 1, 100, 20, 100) : 0;
    const animationDuration = animation ? mapRange(animation.speed, 1, 100, 1000, 50) : 1;

    useEffect(() => {
        if (feColorMatrixRef.current && animationEnabled) {
            if (hueRotateAnimation.current) {
                hueRotateAnimation.current.stop();
            }
            hueRotateMotionValue.set(0);
            hueRotateAnimation.current = animate(hueRotateMotionValue, 360, {
                duration: animationDuration / 25,
                repeat: Infinity,
                repeatType: "loop",
                repeatDelay: 0,
                ease: "linear",
                delay: 0,
                onUpdate: (value) => {
                    if (feColorMatrixRef.current) {
                        feColorMatrixRef.current.setAttribute("values", String(value));
                    }
                }
            });

            return () => {
                if (hueRotateAnimation.current) {
                    hueRotateAnimation.current.stop();
                }
            };
        }
    }, [animationEnabled, animationDuration, hueRotateMotionValue]);

    return (
        <div
            className={className}
            style={{
                overflow: "hidden",
                position: "absolute",
                inset: 0,
                width: "100%",
                height: "100%",
                pointerEvents: "none",
                ...style
            }}
        >
            <div
                style={{
                    position: "absolute",
                    inset: -displacementScale * 2,
                    filter: animationEnabled ? `url(#${id}) blur(40px)` : "none"
                }}
            >
                {animationEnabled && (
                    <svg style={{ position: "absolute", width: "100%", height: "100%" }}>
                        <defs>
                            <filter id={id} x="-50%" y="-50%" width="200%" height="200%">
                                <feTurbulence
                                    result="undulation"
                                    numOctaves="2"
                                    baseFrequency={`${mapRange(animation.scale, 0, 100, 0.003, 0.001)},${mapRange(animation.scale, 0, 100, 0.008, 0.004)}`}
                                    seed="1"
                                    type="turbulence"
                                />
                                <feColorMatrix
                                    ref={feColorMatrixRef}
                                    in="undulation"
                                    type="hueRotate"
                                    values="0"
                                />
                                <feColorMatrix
                                    result="circulation"
                                    type="matrix"
                                    values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -9" // Higher alpha contrast
                                />
                                <feDisplacementMap
                                    in="SourceGraphic"
                                    in2="circulation"
                                    scale={displacementScale * 1.5}
                                    result="dist"
                                />
                                <feDisplacementMap
                                    in="dist"
                                    in2="undulation"
                                    scale={displacementScale}
                                    result="output"
                                />
                            </filter>
                        </defs>
                    </svg>
                )}
                
                {/* 
                    To make the animation visible on BLACK, the Source Graphic 
                    must have a gradient/pattern so the warp is visible across the center.
                */}
                <div
                    style={{
                        position: "absolute",
                        inset: "10%",
                        width: "80%",
                        height: "80%",
                        background: `radial-gradient(circle at center, ${color} 0%, transparent 70%)`,
                        // We add a subtle pattern to ensure the displacement "catches" light internally
                        backgroundImage: `linear-gradient(45deg, ${color} 10%, transparent 40%, ${color} 50%, transparent 90%)`,
                        maskImage: `url('https://framerusercontent.com/images/ceBGguIpUU8luwByxuQz79t7To.png')`,
                        maskSize: sizing === "stretch" ? "100% 100%" : "cover",
                        WebkitMaskImage: `url('https://framerusercontent.com/images/ceBGguIpUU8luwByxuQz79t7To.png')`,
                        WebkitMaskSize: "cover",
                        margin: "auto"
                    }}
                />
            </div>

            {noise && noise.opacity > 0 && (
                <div
                    style={{
                        position: "absolute",
                        inset: 0,
                        backgroundImage: `url("https://framerusercontent.com/images/g0QcWrxr87K0ufOxIUFBakwYA8.png")`,
                        backgroundSize: noise.scale * 200,
                        backgroundRepeat: "repeat",
                        opacity: noise.opacity / 2
                    }}
                />
            )}
        </div>
    );
}
