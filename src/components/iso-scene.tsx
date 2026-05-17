"use client";

import { Canvas, useThree } from "@react-three/fiber";
import { Html, Line, OrbitControls, type OrbitControlsProps } from "@react-three/drei";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";

import {
  PIECE_SYMBOLS,
  pieceAt,
  positionKey,
  positionsEqual,
  type BoardState,
  type Move,
  type Piece,
  type Position,
} from "@/lib/chess";

const CELL_SIZE = 1;
const TILE_THICKNESS = 0.1;
const SLICE_GAP_DEFAULT = 3.4;
const W_GAP_DEFAULT = 2.4;
const PIECE_LIFT = TILE_THICKNESS / 2 + 0.02;

const COLOR_LIGHT_SQUARE = "#eeeed2";
const COLOR_DARK_SQUARE = "#769656";
const COLOR_BASE_PLATE = "#2b2b2b";
const COLOR_SELECTED = "#fde047";
const COLOR_LEGAL = "#22c55e";
const COLOR_CAPTURE = "#ef4444";
const COLOR_HINT = "#f59e0b";
const COLOR_ANALYSIS = "#22d3ee";

type IsoSceneProps = {
  analysisMove: Move | null;
  board: BoardState;
  canHumanMove: boolean;
  hintMove: Move | null;
  onCellClick: (position: Position) => void | Promise<void>;
  selectedMoves: Move[];
  selectedPosition: Position | null;
  spacing: number;
};

export function IsoScene({
  analysisMove,
  board,
  canHumanMove,
  hintMove,
  onCellClick,
  selectedMoves,
  selectedPosition,
  spacing,
}: IsoSceneProps) {
  const cols = board.size[0];
  const rows = board.size[1];
  const sliceCount = board.size[2] ?? 1;
  const wCount = board.dimension >= 4 ? board.size[3] ?? 1 : 1;

  const sliceGap = SLICE_GAP_DEFAULT * spacing;
  const wGap = W_GAP_DEFAULT * spacing;
  const stackHeight = (sliceCount - 1) * sliceGap;
  const stackWidthW = wCount > 1 ? (wCount - 1) * (cols + wGap) : 0;
  const sceneSpan = Math.max(stackWidthW + cols, sliceCount * sliceGap, cols, rows);

  const cameraPosition = useMemo<[number, number, number]>(() => {
    const distance = sceneSpan * 1.45 + 6;
    return [distance * 0.65, distance * 0.55, distance * 0.85];
  }, [sceneSpan]);

  const target = useMemo<[number, number, number]>(() => {
    return [0, stackHeight / 2, 0];
  }, [stackHeight]);

  return (
    <>
      <Canvas
        camera={{ position: cameraPosition, fov: 36, near: 0.1, far: 400 }}
        dpr={[1, 2]}
        shadows
        style={{ width: "100%", height: "100%" }}
      >
        <Suspense fallback={null}>
          <SceneContents
            analysisMove={analysisMove}
            board={board}
            canHumanMove={canHumanMove}
            cameraPosition={cameraPosition}
            cols={cols}
            hintMove={hintMove}
            onCellClick={onCellClick}
            rows={rows}
            selectedMoves={selectedMoves}
            selectedPosition={selectedPosition}
            sliceCount={sliceCount}
            sliceGap={sliceGap}
            target={target}
            wCount={wCount}
            wGap={wGap}
          />
        </Suspense>
      </Canvas>
    </>
  );
}

const SELECTION_BEACON_HEIGHT = 30;

function SceneContents({
  analysisMove,
  board,
  canHumanMove,
  cameraPosition,
  cols,
  hintMove,
  onCellClick,
  rows,
  selectedMoves,
  selectedPosition,
  sliceCount,
  sliceGap,
  target,
  wCount,
  wGap,
}: {
  analysisMove: Move | null;
  board: BoardState;
  canHumanMove: boolean;
  cameraPosition: [number, number, number];
  cols: number;
  hintMove: Move | null;
  onCellClick: (position: Position) => void | Promise<void>;
  rows: number;
  selectedMoves: Move[];
  selectedPosition: Position | null;
  sliceCount: number;
  sliceGap: number;
  target: [number, number, number];
  wCount: number;
  wGap: number;
}) {
  const controlsRef = useRef<OrbitControlsProps>(null);

  useEffect(() => {
    const controls = controlsRef.current;
    if (controls && typeof (controls as { update?: () => void }).update === "function") {
      (controls as { update: () => void }).update();
    }
  }, [target]);

  const slices = useMemo(() => buildSliceDescriptors(board, sliceGap, wGap), [board, sliceGap, wGap]);
  const legalTargetKeys = useMemo(() => {
    const keys = new Set<string>();
    for (const move of selectedMoves) {
      keys.add(positionKey(move.to));
    }
    return keys;
  }, [selectedMoves]);
  const captureTargetKeys = useMemo(() => {
    const keys = new Set<string>();
    for (const move of selectedMoves) {
      const target = pieceAt(board, move.to);
      if (target) {
        keys.add(positionKey(move.to));
      }
    }
    return keys;
  }, [board, selectedMoves]);

  const cellLookup = useMemo(() => {
    const lookup = new Map<string, [number, number, number]>();
    for (const slice of slices) {
      for (let y = 0; y < rows; y += 1) {
        for (let x = 0; x < cols; x += 1) {
          const fullPos: Position = board.dimension === 3
            ? [x, y, slice.z]
            : [x, y, slice.z, slice.w];
          lookup.set(positionKey(fullPos), cellWorldPosition(slice, x, y, cols, rows));
        }
      }
    }
    return lookup;
  }, [board.dimension, cols, rows, slices]);

  return (
    <>
      <ambientLight intensity={0.55} />
      <directionalLight
        castShadow
        intensity={1.1}
        position={[8, 16, 10]}
        shadow-mapSize-height={1024}
        shadow-mapSize-width={1024}
      />
      <hemisphereLight args={["#cfe8ff", "#1f2937", 0.4]} />

      <OrbitControls
        ref={controlsRef as never}
        dampingFactor={0.08}
        enableDamping
        enablePan
        makeDefault
        maxDistance={120}
        minDistance={6}
        target={target}
      />

      {slices.map((slice) => (
        <SliceGroup
          board={board}
          canHumanMove={canHumanMove}
          captureTargetKeys={captureTargetKeys}
          cols={cols}
          key={sliceKey(slice)}
          legalTargetKeys={legalTargetKeys}
          rows={rows}
          selectedPosition={selectedPosition}
          slice={slice}
        />
      ))}

      {hintMove ? (
        <Arrow3D
          color={COLOR_HINT}
          end={cellLookup.get(positionKey(hintMove.to))}
          lineWidth={4}
          start={cellLookup.get(positionKey(hintMove.from))}
        />
      ) : null}
      {analysisMove && (!hintMove || !sameMove(analysisMove, hintMove)) ? (
        <Arrow3D
          color={COLOR_ANALYSIS}
          dashed
          end={cellLookup.get(positionKey(analysisMove.to))}
          lineWidth={2.5}
          start={cellLookup.get(positionKey(analysisMove.from))}
        />
      ) : null}

      <CanvasInputBridge canHumanMove={canHumanMove} onCellClick={onCellClick} />
    </>
  );
}

function CanvasInputBridge({
  canHumanMove,
  onCellClick,
}: {
  canHumanMove: boolean;
  onCellClick: (position: Position) => void | Promise<void>;
}) {
  const { gl, camera, scene } = useThree();
  const raycaster = useMemo(() => new THREE.Raycaster(), []);
  const downRef = useRef<{ x: number; y: number } | null>(null);
  const hoveredRef = useRef<THREE.Object3D | null>(null);

  useEffect(() => {
    const dom = gl.domElement;

    function findCellPosition(intersects: THREE.Intersection[]): Position | null {
      for (const hit of intersects) {
        let walk: THREE.Object3D | null = hit.object;
        while (walk) {
          const userPos = walk.userData?.cellPosition as Position | undefined;
          if (userPos) {
            return userPos;
          }
          walk = walk.parent;
        }
      }
      return null;
    }

    function setRaycaster(event: MouseEvent | PointerEvent) {
      const rect = dom.getBoundingClientRect();
      const ndc = new THREE.Vector2(
        ((event.clientX - rect.left) / rect.width) * 2 - 1,
        -((event.clientY - rect.top) / rect.height) * 2 + 1,
      );
      raycaster.setFromCamera(ndc, camera);
    }

    function clearHovered() {
      const previous = hoveredRef.current;
      if (previous) {
        previous.userData?.setHovered?.(false);
        hoveredRef.current = null;
      }
      dom.style.cursor = "default";
    }

    function onPointerDown(event: PointerEvent) {
      if (event.button !== 0) return;
      downRef.current = { x: event.clientX, y: event.clientY };
    }

    function onClick(event: MouseEvent) {
      const down = downRef.current;
      downRef.current = null;
      if (down) {
        const dx = Math.abs(event.clientX - down.x);
        const dy = Math.abs(event.clientY - down.y);
        if (dx > 5 || dy > 5) return;
      }
      setRaycaster(event);
      const hits = raycaster.intersectObjects(scene.children, true);
      const pos = findCellPosition(hits);
      if (pos) {
        void onCellClick(pos);
      }
    }

    function onPointerMove(event: PointerEvent) {
      setRaycaster(event);
      const hits = raycaster.intersectObjects(scene.children, true);
      let target: THREE.Object3D | null = null;
      for (const hit of hits) {
        let walk: THREE.Object3D | null = hit.object;
        while (walk) {
          if (walk.userData?.cellPosition) {
            target = walk;
            break;
          }
          walk = walk.parent;
        }
        if (target) break;
      }

      if (target !== hoveredRef.current) {
        hoveredRef.current?.userData?.setHovered?.(false);
        target?.userData?.setHovered?.(true);
        hoveredRef.current = target;
        dom.style.cursor = target && canHumanMove ? "pointer" : "default";
      }
    }

    function onPointerLeave() {
      clearHovered();
      downRef.current = null;
    }

    dom.addEventListener("pointerdown", onPointerDown);
    dom.addEventListener("click", onClick);
    dom.addEventListener("pointermove", onPointerMove);
    dom.addEventListener("pointerleave", onPointerLeave);
    return () => {
      dom.removeEventListener("pointerdown", onPointerDown);
      dom.removeEventListener("click", onClick);
      dom.removeEventListener("pointermove", onPointerMove);
      dom.removeEventListener("pointerleave", onPointerLeave);
      clearHovered();
    };
  }, [camera, canHumanMove, gl.domElement, onCellClick, raycaster, scene]);

  return null;
}

type SliceDescriptor = {
  z: number;
  w: number;
  origin: [number, number, number];
  label: string;
};

function buildSliceDescriptors(board: BoardState, sliceGap: number, wGap: number): SliceDescriptor[] {
  const cols = board.size[0];
  const sliceCount = board.size[2] ?? 1;
  const wCount = board.dimension >= 4 ? board.size[3] ?? 1 : 1;
  const result: SliceDescriptor[] = [];

  for (let w = 0; w < wCount; w += 1) {
    const baseX = (w - (wCount - 1) / 2) * (cols + wGap);
    for (let z = 0; z < sliceCount; z += 1) {
      result.push({
        z,
        w,
        origin: [baseX, z * sliceGap, 0],
        label: board.dimension === 3 ? `z=${z}` : `z=${z} · w=${w}`,
      });
    }
  }
  return result;
}

function sliceKey(slice: SliceDescriptor): string {
  return `slice-${slice.w}-${slice.z}`;
}

function cellWorldPosition(
  slice: SliceDescriptor,
  x: number,
  y: number,
  cols: number,
  rows: number,
): [number, number, number] {
  const localX = (x - (cols - 1) / 2) * CELL_SIZE;
  const localZ = ((rows - 1) / 2 - y) * CELL_SIZE;
  return [slice.origin[0] + localX, slice.origin[1], slice.origin[2] + localZ];
}

function SliceGroup({
  board,
  canHumanMove,
  captureTargetKeys,
  cols,
  legalTargetKeys,
  rows,
  selectedPosition,
  slice,
}: {
  board: BoardState;
  canHumanMove: boolean;
  captureTargetKeys: Set<string>;
  cols: number;
  legalTargetKeys: Set<string>;
  rows: number;
  selectedPosition: Position | null;
  slice: SliceDescriptor;
}) {
  const cells: React.ReactElement[] = [];
  for (let y = 0; y < rows; y += 1) {
    for (let x = 0; x < cols; x += 1) {
      const position: Position = board.dimension === 3
        ? [x, y, slice.z]
        : [x, y, slice.z, slice.w];
      const key = positionKey(position);
      cells.push(
        <Cell
          board={board}
          canHumanMove={canHumanMove}
          col={x}
          cols={cols}
          isCapture={captureTargetKeys.has(key)}
          isLegal={legalTargetKeys.has(key)}
          isSelected={Boolean(selectedPosition && positionsEqual(selectedPosition, position))}
          key={key}
          position={position}
          row={y}
          rows={rows}
        />,
      );
    }
  }

  return (
    <group position={slice.origin}>
      <mesh
        position={[0, -TILE_THICKNESS / 2 - 0.02, 0]}
        receiveShadow
      >
        <boxGeometry args={[cols + 0.4, 0.05, rows + 0.4]} />
        <meshStandardMaterial color={COLOR_BASE_PLATE} metalness={0.1} roughness={0.85} />
      </mesh>

      {cells}

      <Html
        center
        distanceFactor={12}
        pointerEvents="none"
        position={[(cols / 2) + 0.1, 0.4, -(rows / 2) - 0.1]}
        wrapperClass="iso-html-passthrough"
        style={{
          pointerEvents: "none",
          fontSize: "12px",
          fontWeight: 800,
          letterSpacing: "0.04em",
          color: "#fff",
          background: "rgba(15, 23, 42, 0.85)",
          padding: "3px 7px",
          border: "1px solid rgba(245, 158, 11, 0.6)",
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          userSelect: "none",
        }}
      >
        {slice.label}
      </Html>
    </group>
  );
}

function Cell({
  board,
  canHumanMove,
  col,
  cols,
  isCapture,
  isLegal,
  isSelected,
  position,
  row,
  rows,
}: {
  board: BoardState;
  canHumanMove: boolean;
  col: number;
  cols: number;
  isCapture: boolean;
  isLegal: boolean;
  isSelected: boolean;
  position: Position;
  row: number;
  rows: number;
}) {
  const [hovered, setHovered] = useState(false);
  const meshRef = useRef<THREE.Mesh>(null);
  const piece = pieceAt(board, position);
  const localX = (col - (cols - 1) / 2) * CELL_SIZE;
  const localZ = ((rows - 1) / 2 - row) * CELL_SIZE;
  const baseColor = (col + row) % 2 === 0 ? COLOR_DARK_SQUARE : COLOR_LIGHT_SQUARE;
  const emissive = isSelected
    ? COLOR_SELECTED
    : isCapture
      ? COLOR_CAPTURE
      : isLegal
        ? COLOR_LEGAL
        : hovered && canHumanMove
          ? "#facc15"
          : "#000000";
  const emissiveIntensity = isSelected ? 0.7 : isCapture ? 0.45 : isLegal ? 0.4 : hovered && canHumanMove ? 0.22 : 0;

  useEffect(() => {
    const mesh = meshRef.current;
    if (!mesh) return;
    mesh.userData.cellPosition = position;
    mesh.userData.setHovered = setHovered;
    return () => {
      if (mesh.userData) {
        delete mesh.userData.cellPosition;
        delete mesh.userData.setHovered;
      }
    };
  }, [position]);

  const cellMaterial = useMemo(() => {
    const mat = new THREE.MeshStandardMaterial({
      color: baseColor,
      emissive,
      emissiveIntensity,
      metalness: 0.05,
      roughness: 0.78,
    });
    return mat;
  }, []);

  useEffect(() => {
    cellMaterial.color.set(baseColor);
    cellMaterial.emissive.set(emissive);
    cellMaterial.emissiveIntensity = emissiveIntensity;
    cellMaterial.needsUpdate = true;
  }, [baseColor, cellMaterial, emissive, emissiveIntensity]);

  useEffect(() => {
    return () => {
      cellMaterial.dispose();
    };
  }, [cellMaterial]);

  return (
    <group position={[localX, 0, localZ]}>
      <mesh
        ref={meshRef}
        castShadow
        receiveShadow
      >
        <boxGeometry args={[CELL_SIZE * 0.97, TILE_THICKNESS, CELL_SIZE * 0.97]} />
        <primitive object={cellMaterial} attach="material" />
      </mesh>

      {isLegal && !isCapture ? (
        <mesh position={[0, TILE_THICKNESS / 2 + 0.005, 0]}>
          <cylinderGeometry args={[0.18, 0.18, 0.02, 24]} />
          <meshStandardMaterial color={COLOR_LEGAL} emissive={COLOR_LEGAL} emissiveIntensity={0.6} />
        </mesh>
      ) : null}

      {isCapture ? (
        <mesh position={[0, TILE_THICKNESS / 2 + 0.005, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.36, 0.46, 32]} />
          <meshStandardMaterial color={COLOR_CAPTURE} emissive={COLOR_CAPTURE} emissiveIntensity={0.7} side={THREE.DoubleSide} />
        </mesh>
      ) : null}

      {isSelected ? (
        <>
          <mesh position={[0, TILE_THICKNESS / 2 + 0.01, 0]} rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.42, 0.5, 48]} />
            <meshBasicMaterial color={COLOR_SELECTED} side={THREE.DoubleSide} toneMapped={false} />
          </mesh>
          <mesh position={[0, SELECTION_BEACON_HEIGHT / 2, 0]}>
            <boxGeometry args={[0.05, SELECTION_BEACON_HEIGHT, 0.05]} />
            <meshBasicMaterial
              color={COLOR_SELECTED}
              toneMapped={false}
              transparent
              opacity={0.9}
            />
          </mesh>
        </>
      ) : null}

      {piece ? <PieceGlyph piece={piece} /> : null}
    </group>
  );
}

function PieceGlyph({ piece }: { piece: Piece }) {
  const symbol = PIECE_SYMBOLS[piece.color][piece.kind];
  return (
    <Html
      center
      distanceFactor={9}
      pointerEvents="none"
      position={[0, PIECE_LIFT, 0]}
      wrapperClass="iso-html-passthrough"
      style={{
        pointerEvents: "none",
        userSelect: "none",
        fontSize: "44px",
        lineHeight: 1,
        color: piece.color === "white" ? "#ffffff" : "#111111",
        textShadow:
          piece.color === "white"
            ? "0 1px 2px rgba(0,0,0,0.85)"
            : "0 1px 0 rgba(255,255,255,0.4)",
        fontFamily:
          'Arial, "Helvetica Neue", Helvetica, "Segoe UI Symbol", "DejaVu Sans", sans-serif',
        fontWeight: 700,
        whiteSpace: "nowrap",
      }}
    >
      {symbol}
    </Html>
  );
}

function Arrow3D({
  color,
  dashed = false,
  end,
  lineWidth,
  start,
}: {
  color: string;
  dashed?: boolean;
  end: [number, number, number] | undefined;
  lineWidth: number;
  start: [number, number, number] | undefined;
}) {
  if (!start || !end) {
    return null;
  }

  const startV = new THREE.Vector3(...start);
  const endV = new THREE.Vector3(...end);
  const distance = startV.distanceTo(endV);
  const arcHeight = Math.min(2.5, 0.4 + distance * 0.18);
  const mid = new THREE.Vector3().addVectors(startV, endV).multiplyScalar(0.5);
  mid.y += arcHeight;
  const baseLift = 0.25;
  const lift = new THREE.Vector3(0, baseLift, 0);
  const liftedStart = startV.clone().add(lift);
  const liftedEnd = endV.clone().add(lift);
  const curve = new THREE.QuadraticBezierCurve3(liftedStart, mid, liftedEnd);
  const samples = 48;
  const points: [number, number, number][] = [];
  for (let i = 0; i <= samples; i += 1) {
    const point = curve.getPoint(i / samples);
    points.push([point.x, point.y, point.z]);
  }

  const tangent = curve.getTangent(1).normalize();
  const arrowLength = 0.6;
  const arrowQuat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), tangent);
  const arrowEuler = new THREE.Euler().setFromQuaternion(arrowQuat);
  const arrowBase = liftedEnd.clone().sub(tangent.clone().multiplyScalar(arrowLength * 0.5));

  return (
    <group>
      <Line
        color={color}
        dashed={dashed}
        dashScale={4}
        dashSize={0.35}
        gapSize={0.18}
        lineWidth={lineWidth}
        points={points}
        transparent
        opacity={0.95}
      />
      <mesh position={[arrowBase.x, arrowBase.y, arrowBase.z]} rotation={[arrowEuler.x, arrowEuler.y, arrowEuler.z]}>
        <coneGeometry args={[0.22, arrowLength, 18]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.6} />
      </mesh>
    </group>
  );
}

function sameMove(left: Move, right: Move): boolean {
  return positionsEqual(left.from, right.from) && positionsEqual(left.to, right.to);
}
