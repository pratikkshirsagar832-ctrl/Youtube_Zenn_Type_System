import React from "react";
import { AbsoluteFill } from "remotion";
import { PsycheCharacter, PsycheExpression, PsychePosition, PsycheAnimation } from "./PsycheCharacter";
import { GenericCharacter } from "./GenericCharacter";
import { ZennBackground, BackgroundElement } from "./ZennBackground";
import { SubtitleLayer, SubtitleWord } from "../SubtitleLayer";
import { propComponents } from "./PropComponents";

export interface SceneData {
  scene_id: number;
  duration_seconds: number;
  scene_type: string;
  character_expression: PsycheExpression;
  character_position: PsychePosition;
  character_animation: PsycheAnimation;
  background: {
    bg_color: string;
    elements: BackgroundElement[];
  };
  props: string[];
  prop_position: string;
  num_characters: number;
  motion_type: string;
  subtitle_words: SubtitleWord[];
}

interface SceneRendererProps {
  scene: SceneData;
}

export const SceneRenderer: React.FC<SceneRendererProps> = ({ scene }) => {
  const PropComponent = scene.props.length > 0 ? propComponents[scene.props[0]] : null;

  const propStyle: React.CSSProperties =
    scene.prop_position === "left_of_character"
      ? { position: "absolute", left: "5%", top: "35%", transform: "translateY(-50%)" }
      : scene.prop_position === "above"
        ? { position: "absolute", left: "50%", top: "15%", transform: "translateX(-50%)" }
        : { position: "absolute", right: "8%", top: "35%", transform: "translateY(-50%)" };

  return (
    <AbsoluteFill>
      {scene.background && (
        <ZennBackground
          bg_color={scene.background.bg_color}
          elements={scene.background.elements}
        />
      )}

      {PropComponent && (
        <div style={propStyle}>
          <PropComponent size={70} />
        </div>
      )}

      {scene.num_characters >= 1 && (
        <PsycheCharacter
          expression={scene.character_expression}
          position={scene.character_position}
          animation={scene.character_animation}
          size={250}
        />
      )}

      {scene.num_characters === 2 && (
        <GenericCharacter position="right" size={220} />
      )}

      <SubtitleLayer words={scene.subtitle_words} />
    </AbsoluteFill>
  );
};
