# Neural Architecture Exchange Specification (NAXS)

**Version:** 0.1  
**Status:** Draft for Public Review  
**License:** CC-BY-4.0 / Apache-2.0 (dual)  
**Repository:** https://github.com/neuroarchitectures/naxs  
**Created:** 2026-09-23  

---

## Table of Contents

| # | Section | What It Covers |
|---|---------|---------------|
| 1 | [Abstract](#1-abstract) | What NAXS is and is not |
| 2 | [Design Principles](#2-design-principles) | Six core principles |
| 3 | [Relationship to Other Formats](#3-relationship-to-other-formats) | ONNX, PyTorch, MLIR comparison |
| 4 | [Document Structure](#4-document-structure) | Top-level JSON fields |
| 5 | [Component (Node)](#5-component-node) | Node definition, required/optional fields |
| 6 | [Parameters](#6-parameters) | Value types, symbolic dims, naming |
| 7 | [Operator Type Registry](#7-operator-type-registry) | 79 standard types + custom |
| 8 | [Connection (Edge)](#8-connection-edge) | Edge definition, redundancy rules |
| 9 | [Metadata](#9-metadata) | Vendor-specific info |
| 10 | [Provenance](#10-provenance) | Origin tracking |
| 11 | [Extension Model](#11-extension-model) | Vendor extensions, versioning |
| 12 | [Scope Notation](#12-scope-notation) | Hierarchical grouping |
| 13 | [Validation Rules](#13-validation-rules) | 15 rules + soft validation |
| 14 | [Minimal Example](#14-minimal-example) | Smallest valid document |
| 15–19 | [Full Examples](#15-full-example-bert-base-excerpt) | BERT, ResNet, Llama, Mamba, 3DGS |
| 20 | [Conformance](#20-conformance) | Producer / Consumer / Validator |
| 21 | [JSON Schema](#21-json-schema) | Machine-readable schema |
| 22 | [Migration from Atlas model.json](#22-migration-from-atlas-modeljson) | Field mapping table |
| 23 | [Glossary](#23-glossary) | Term definitions |
| 24 | [Change Log](#24-change-log) | Version history |
| 25 | [Block Templates & Repetition](#25-block-templates-and-repetition) | Reusable subgraphs, repeat directives |
| A | [Standard Parameter Name Catalog](#appendix-a-standard-parameter-name-catalog) | All standard params by type |
| B | [Operator Type Frequency](#appendix-b-operator-type-frequency) | Statistics from 288 architectures |
| C | [Scope Pattern Catalog](#appendix-c-scope-pattern-catalog) | Common scope patterns |
| D | [Implementation Notes](#appendix-d-implementation-notes) | Parsing, graph, coercion, round-trip |

---

## Quick Reference Card

> **For agents coding against this spec:** Start here. Everything below is the full detail.

**NAXS = a JSON file describing a neural architecture as a directed graph.**

```json
{
  "spec_version": "0.1",          // REQUIRED — must be "0.1"
  "id": "my-arch",                // REQUIRED — URL-safe slug
  "name": "My Architecture",      // REQUIRED — display name
  "components": [ ... ],          // REQUIRED — graph nodes (≥1)
  "connections": [ ... ],         // REQUIRED — graph edges (may be empty)
  "description": "...",           // optional
  "block_templates": [ ... ],     // optional — see §25
  "metadata": { ... },            // optional — vendor info
  "provenance": { ... }           // optional — origin info
}
```

**Component (node):**
```json
{
  "id": "n1",                     // REQUIRED — unique, no dots/whitespace
  "type": "conv2d",               // REQUIRED — operator type (§7)
  "name": "Conv1",                // REQUIRED — display name
  "params": { "inChannels": 3 }, // REQUIRED — may be {}
  "inputs": ["n0"],              // REQUIRED — source IDs
  "outputs": ["n2"],             // REQUIRED — target IDs
  "scope": "backbone.layer.0",   // optional — dot-separated hierarchy
  "position": { "x": 100, "y": 200 }, // optional — visual only
  "block_ref": "template_id",    // optional — see §25.3
  "repeat": { "count": 12 }      // optional — see §25.4
}
```

**Connection (edge):**
```json
{
  "id": "c1",                     // REQUIRED — unique
  "from": "n1",                  // REQUIRED — source component ID
  "to": "n2",                    // REQUIRED — target component ID
  "fromPort": "bottom",          // optional — visual hint
  "toPort": "top"                // optional — visual hint
}
```

**Parameter values allowed:** `integer`, `float`, `boolean`, `string`, `array` (of int/string).  
**NOT allowed:** `null`, nested objects, arrays of arrays.

**Key rules at a glance:**
- Component `inputs`/`outputs` and `connections` array MUST be consistent (§13.2).
- Unknown fields MUST be preserved (§4.3, §5.3).
- Unknown operator types MUST NOT cause failure (§7.3).
- Graph MAY be cyclic (§13.2, rule 11).
- Block templates expand to standard components (§25).

---

## 1. Abstract

The **Neural Architecture Exchange Specification (NAXS)** defines a vendor-independent, framework-agnostic JSON format for describing neural network architectures as directed graphs of typed, parameterized components.

NAXS is **not** an execution format (like ONNX), a training configuration (like PyTorch Lightning YAML), or a compiler IR (like MLIR). It is an **architecture topology exchange format**: it describes *what the architecture is* — its components, their parameters, and their connectivity — without prescribing *how* it runs.

The goal is interoperability: any tool, vendor, research group, or automated agent can produce or consume a NAXS document to share, compare, transform, or analyze a neural architecture without depending on a specific framework.

---

## 2. Design Principles

1. **Framework-independent.** The format references operator types by name (e.g. `conv2d`, `multiHeadAttention`), not by framework API (`torch.nn.Conv2d`, `flax.linen.Conv`).
2. **Graph-first.** An architecture is a directed graph. Connectivity is explicit, not implicit in code structure.
3. **Parameterized.** Each component carries typed parameters. The same operator type produces different concrete nodes depending on parameter values.
4. **Human-readable.** The JSON is verbose but simple. A human can read and hand-author a NAXS document without specialized tooling.
5. **Extensible.** Unknown fields are preserved, not rejected. Vendors can add metadata without breaking consumers.
6. **Minimal core.** The required fields are few. Everything else is optional. A valid NAXS document can be as small as 10 lines.

---

## 3. Relationship to Other Formats

| Format | Purpose | NAXS Relationship |
|--------|---------|-------------------|
| **ONNX** | Executable computation graph | NAXS describes architecture topology; ONNX describes runtime computation. A NAXS document can be *lowered* to ONNX via implementation bindings. |
| **PyTorch `config.json`** | Model-specific configuration | NAXS is model-agnostic; one format for all architectures. PyTorch configs can be *imported* into NAXS. |
| **HuggingFace `model.safetensors`** | Weight checkpoint | NAXS explicitly excludes weights. Weights are external artifacts referenced by metadata. |
| **MLIR** | Compiler intermediate representation | NAXS is a higher-level exchange format. MLIR can be a compilation target. |
| **Netron JSON** | Visualization metadata | NAXS includes visual position hints but is not a visualization format. |

---

## 4. Document Structure

A NAXS document is a single JSON object with the following top-level structure:

```json
{
  "$schema": "https://raw.githubusercontent.com/neuroarchitectures/naxs/main/naxs/v0.1/schema.json",
  "spec_version": "0.1",
  "id": "bert-base",
  "name": "BERT-Base",
  "description": "BERT-Base: 12-layer transformer encoder, hidden size 768.",
  "components": [ ... ],
  "connections": [ ... ]
}
```

### 4.1 Required Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `spec_version` | string | NAXS specification version. Must be `"0.1"`. |
| `id` | string | Unique architecture identifier. Should be a URL-safe slug (e.g. `"bert-base"`, `"resnet-50"`). |
| `name` | string | Human-readable display name. |
| `components` | array | List of component objects (the graph nodes). Must contain at least one component. |
| `connections` | array | List of connection objects (the graph edges). May be empty if connectivity is fully described by component `inputs`/`outputs`. |

### 4.2 Optional Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Free-text description of the architecture. |
| `category` | string | Domain category (e.g. `"Computer Vision"`, `"NLP"`, `"Recommendation"`). |
| `icon` | string | Emoji or icon name for UI display. |
| `real_param_count` | integer | Real-world parameter count (for evaluation/cross-check). |
| `block_templates` | array | Reusable subgraph definitions. See [§25](#25-block-templates-and-repetition). |
| `metadata` | object | Arbitrary vendor-specific metadata. See [§9](#9-metadata). |
| `provenance` | object | Origin information. See [§10](#10-provenance). |

### 4.3 Extension Fields

Any top-level field not listed above **MUST** be preserved by conforming consumers. Unknown fields **MUST NOT** cause parsing failure. This enables vendors to embed custom metadata without forking the spec.

> **For Implementers:** Use a JSON parser that preserves unknown fields (e.g. serde's `#[serde(flatten)]` in Rust, `**kwargs` in Python). Never use a strict schema that drops unknown keys.

---

## 5. Component (Node)

A component is a single node in the architecture graph. It represents one operator instance with concrete parameters.

```json
{
  "id": "n3",
  "type": "multiHeadAttention",
  "name": "Attention_1",
  "params": {
    "numHeads": 12,
    "hiddenDim": 768
  },
  "inputs": ["n2"],
  "outputs": ["n4"],
  "scope": "layer.0.attention"
}
```

### 5.1 Required Component Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique component identifier within the document. Must be referenced by at least one connection or by another component's `inputs`/`outputs`. |
| `type` | string | Operator type identifier. See [§7](#7-operator-type-registry) for the operator type registry. |
| `name` | string | Human-readable display name for this instance. |
| `params` | object | Parameter key-value map. May be empty `{}`. See [§6](#6-parameters). |
| `inputs` | array of strings | IDs of components that feed into this component. May be empty for input/source nodes. |
| `outputs` | array of strings | IDs of components this component feeds into. May be empty for output/sink nodes. |

### 5.2 Optional Component Fields

| Field | Type | Description |
|-------|------|-------------|
| `scope` | string | Hierarchical scope path using dot notation (e.g. `"layer.0.attention"`, `"encoder.block.1.ffn"`). Enables grouping and hierarchical analysis. See [§12](#12-scope-notation). |
| `position` | object | Visual layout position `{ "x": number, "y": number }`. Rendering hint only; has no architectural semantics. |
| `input_shape` | array | Declared input tensor shape (e.g. `[1, 512, 768]`). May contain symbolic strings (e.g. `["batch", "seq_len", 768]`). |
| `notes` | string | Free-text annotation for this component. |
| `repeat` | object | Repetition directive: expand this component into N copies. See [§25.4](#254-repeat-directive). |
| `block_ref` | string | Reference to a block template by `id`. See [§25.3](#253-block-reference-components). |

### 5.3 Extension Fields

Any component field not listed above **MUST** be preserved by conforming consumers.

### 5.4 Component ID Rules

- IDs must be unique within a document.
- IDs should be short and stable (e.g. `"n1"`, `"n2"`, `"embed"`, `"attn_1"`).
- IDs must not contain whitespace or the `.` character (reserved for scope notation).
- Renumbering IDs is a valid transformation; consumers must follow references, not positions.

> **For Implementers:** The `.` character is reserved because expanded block-template node IDs use dot notation (e.g. `layer_0.attn`). If you encounter a `.` in an ID, it likely comes from block expansion — see [§25.3](#253-block-reference-components).

---

## 6. Parameters

Parameters describe the concrete configuration of a component. They are architectural configuration, **not** runtime weights.

### 6.1 Parameter Value Types

A parameter value may be any of the following JSON types:

| JSON Type | Example | Semantic Meaning |
|-----------|---------|------------------|
| integer | `768` | A scalar integer (e.g. `hiddenDim`, `numHeads`, `vocabSize`). |
| float | `0.02` | A scalar floating-point number (e.g. dropout rate, scaling factor). |
| boolean | `true` | A boolean flag (e.g. `bias`, `residual`). |
| string | `"gelu"` | An enumeration or named choice (e.g. activation function name). |
| array | `[3, 224, 224]` | A tensor shape or multi-dimensional value (e.g. `kernelSize`, `shape`). Array elements may be integers or strings (symbolic dimensions). |

### 6.2 Symbolic Dimensions

Array parameters may contain string elements to represent symbolic (dynamic) dimensions:

```json
"params": {
  "shape": ["batch", "seq_len", 768]
}
```

Consumers should treat string elements as symbolic identifiers and integer elements as fixed dimensions.

### 6.3 Parameter Naming Conventions

NAXS does not enforce a parameter naming convention. Parameter names are operator-type-specific. However, the following conventions are **recommended** for consistency:

| Convention | Examples |
|------------|----------|
| camelCase | `numHeads`, `hiddenDim`, `embeddingDim`, `kernelSize` |
| Descriptive | `vocabSize`, `inChannels`, `outChannels`, `ffDim` |
| Boolean flags | `bias`, `residual`, `training` |

A registry of standard parameter names per operator type is provided in [§7](#7-operator-type-registry) and [Appendix A](#appendix-a-standard-parameter-name-catalog).

### 6.4 Parameters vs. Weights

Parameters are **architectural configuration**: they define the shape and behavior of the operator. Examples: `numHeads=12`, `hiddenDim=768`, `kernelSize=3`.

Weights are **trained values**: they are the learned parameters of the model. Examples: attention weight matrices, embedding lookup tables, convolution filters.

NAXS documents **MUST NOT** contain weight values. Weight references (e.g. checkpoint paths) may appear in `metadata` but are not part of the architecture specification.

---

## 7. Operator Type Registry

NAXS maintains a registry of standard operator types. Each type defines a name, a set of expected parameters, and typical input/output arity.

### 7.1 Standard Operator Types

The following types are recognized in NAXS 0.1. Types not in this list are treated as `custom` — consumers should preserve them but may not interpret their parameters.

#### Core / I/O

| Type | Description | Key Parameters |
|------|-------------|----------------|
| `input` | Input source (data source, token stream, image) | `shape` |
| `output` | Output sink (prediction, representation) | — |
| `custom` | Vendor-defined or composite operator | (free-form) |

#### Linear / Projection

| Type | Description | Key Parameters |
|------|-------------|----------------|
| `linear` | Fully-connected / dense layer | `inFeatures`, `outFeatures`, `bias` |
| `embedding` | Token / position embedding lookup | `vocabSize`, `embeddingDim`, `maxSeqLen`, `numEmbeddings` |
| `embed` | Generic embedding (graph, feature) | — |

#### Convolution

| Type | Description | Key Parameters |
|------|-------------|----------------|
| `conv2d` | 2D convolution | `inChannels`, `outChannels`, `kernelSize`, `stride`, `padding` |
| `depthwiseConv2d` | Depthwise separable 2D conv | `inChannels`, `outChannels`, `kernelSize`, `stride`, `padding` |
| `conv1d` | 1D convolution (audio, temporal) | `inChannels`, `outChannels`, `kernelSize`, `stride`, `padding` |
| `conv3d` | 3D convolution (video, volumetric) | `inChannels`, `outChannels`, `kernelSize`, `stride`, `padding` |
| `deformableConv2d` | Deformable 2D convolution | `inChannels`, `outChannels`, `kernelSize` |

#### Attention

| Type | Description | Key Parameters |
|------|-------------|----------------|
| `multiHeadAttention` | Multi-head self/cross attention | `numHeads`, `hiddenDim` |
| `groupedQueryAttention` | Grouped-query attention (GQA) | `embedDim`, `numHeads`, `numKVHeads`, `headDim` |
| `crossAttention` | Cross-attention between two streams | `numHeads`, `hiddenDim` |
| `attention` | Generic attention (unspecified variant) | — |
| `mla` | Multi-head latent attention (DeepSeek MLA) | `kvLatentDim`, `qLatentDim`, `ropeHeadDim` |

#### Normalization

| Type | Description | Key Parameters |
|------|-------------|----------------|
| `layerNorm` | Layer normalization | `normalizedShape` |
| `rmsNorm` | Root mean square normalization | `normalizedShape` |
| `batchNorm` | Batch normalization | `numFeatures` |
| `groupNorm` | Group normalization | `numGroups`, `numChannels` |

#### Activation

| Type | Description | Key Parameters |
|------|-------------|----------------|
| `relu` | ReLU activation | — |
| `gelu` | GELU activation | — |
| `swish` | SiLU / Swish activation | — |
| `silu` | SiLU activation (alias of `swish`) | — |

#### Feed-Forward / MLP

| Type | Description | Key Parameters |
|------|-------------|----------------|
| `feedForward` | Standard feed-forward network | `hiddenDim`, `ffDim` |
| `ffn` | Generic feed-forward (alias) | — |
| `swiglu` | SwiGLU FFN | `intermediateSize`, `dim` |
| `geglu` | GeGLU FFN | `intermediateSize`, `dim` |

#### Structural

| Type | Description | Key Parameters |
|------|-------------|----------------|
| `add` | Element-wise addition (residual connection) | — |
| `residual` | Residual connection wrapper | — |
| `concatenate` | Tensor concatenation | — |
| `multiply` | Element-wise multiplication (gating) | — |
| `transformerBlock` | Composite transformer block | `embedDim`, `numHeads`, `ffDim` |

#### Specialized

| Type | Description | Key Parameters |
|------|-------------|----------------|
| `moeLayer` | Mixture of experts layer | `numExperts`, `expertDim`, `topK` |
| `sharedExpertMoE` | MoE with shared experts | `numExperts`, `expertDim`, `topK`, `numSharedExperts` |
| `patchEmbed` | Patch embedding (ViT) | `imgSize`, `patchSize`, `embedDim`, `inChans` |
| `seBlock` | Squeeze-and-excitation block | `channels`, `reduction` |
| `gcn_conv` | Graph convolution layer | — |
| `rope` | Rotary position embedding | — |

### 7.2 Custom Operator Types

Vendors MAY define custom operator types by using the `custom` type and providing a `name` that describes the operator. Consumers MUST preserve custom operators but MAY treat them as opaque.

For vendor-specific operators that should be interoperable, vendors SHOULD register new types through the NAXS extension process (see [§11](#11-extension-model)).

### 7.3 Operator Type Extensibility

New operator types are added through the extension process. The registry is versioned alongside the spec version. Consumers MUST NOT fail when encountering unknown types; they SHOULD treat unknown types as opaque nodes with their parameters preserved.

> **For Implementers:** When you encounter an unknown `type`, do not crash. Store the component as an opaque node with its `params` preserved. Use the `name` field as a human-readable label. This is critical for forward compatibility.

---

## 8. Connection (Edge)

A connection represents a directed edge in the architecture graph, from one component's output to another component's input.

```json
{
  "id": "c1",
  "from": "n1",
  "to": "n2",
  "fromPort": "bottom",
  "toPort": "top"
}
```

### 8.1 Required Connection Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique connection identifier within the document. |
| `from` | string | ID of the source component. |
| `to` | string | ID of the target component. |

### 8.2 Optional Connection Fields

| Field | Type | Description |
|-------|------|-------------|
| `fromPort` | string | Source port label (rendering hint). Common values: `"bottom"`, `"right"`, `"output_0"`. |
| `toPort` | string | Target port label (rendering hint). Common values: `"top"`, `"left"`, `"input_0"`. |

### 8.3 Connection Semantics

- A connection indicates that data flows from `from` to `to`.
- The `fromPort`/`toPort` fields are **visual rendering hints**, not semantic port identities. They describe where on the visual node the edge connects, not which logical port is used.
- Multiple connections from the same source to different targets are allowed (fan-out).
- Multiple connections from different sources to the same target are allowed (fan-in / merge).
- Self-loops (where `from == to`) are allowed but should be documented.

### 8.4 Redundancy with Component inputs/outputs

The `connections` array and the component `inputs`/`outputs` fields encode the same connectivity information in two forms:

- **Component `inputs`/`outputs`**: adjacency lists. `outputs` of component A lists the IDs of components that A feeds into. `inputs` of component B lists the IDs of components that feed into B.
- **`connections` array**: explicit edge objects with IDs and port labels.

Both forms **MUST** be consistent. If component A lists `"n5"` in its `outputs`, then there **MUST** be a connection `{ "from": "A", "to": "n5" }` in the `connections` array, and vice versa.

Consumers MAY use either form for graph construction but SHOULD verify consistency.

> **For Implementers:** You can build the graph from either `connections` or `inputs`/`outputs` alone, but you SHOULD verify both forms agree. See [§13.2](#132-consistency), rules 9–10.

### 8.5 Port-Level Connectivity (Future Extension)

NAXS 0.1 uses node-level connectivity (edges connect components, not specific ports). A future version may introduce explicit port references:

```json
{
  "from": "n4",
  "fromPort": "output_0",
  "to": "n5",
  "toPort": "input_1"
}
```

where `output_0` and `input_1` are semantic port identifiers defined by the operator type. This is reserved for future versions.

---

## 9. Metadata

The `metadata` object provides vendor-specific information that does not affect architectural semantics.

```json
{
  "metadata": {
    "framework": "pytorch",
    "framework_version": "2.1.0",
    "paper": "https://arxiv.org/abs/1810.04805",
    "checkpoint": "https://huggingface.co/bert-base-uncased",
    "license": "apache-2.0",
    "tags": ["encoder", "transformer", "nlp"]
  }
}
```

Metadata fields are not standardized by NAXS. Consumers MUST preserve all metadata fields. Common conventions:

| Field | Type | Description |
|-------|------|-------------|
| `framework` | string | Source framework (e.g. `"pytorch"`, `"jax"`, `"tensorflow"`) |
| `framework_version` | string | Framework version |
| `paper` | string | URL to the original paper |
| `checkpoint` | string | URL or path to weight checkpoint |
| `license` | string | License identifier |
| `tags` | array of strings | Free-form tags |

---

## 10. Provenance

The `provenance` object records the origin and transformation history of the document.

```json
{
  "provenance": {
    "source": "atlas/architectures/bert-base/model.json",
    "imported_at": "2026-09-22T12:00:00Z",
    "imported_by": "anad-atlas v0.1.0",
    "original_format": "atlas-model-json",
    "transformations": []
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `source` | string | Path or URL to the original source document. |
| `imported_at` | string | ISO 8601 timestamp of import. |
| `imported_by` | string | Tool and version that produced this document. |
| `original_format` | string | Format of the source (e.g. `"atlas-model-json"`, `"pytorch-config"`, `"onnx"`, `"manual"`). |
| `transformations` | array | List of transformation steps applied. Each entry is an object with `operation`, `timestamp`, and `description`. |

Provenance is optional. When present, it enables traceability and reproducibility.

---

## 11. Extension Model

### 11.1 Vendor Extensions

Vendors MAY add custom fields at any level (top-level, component, connection) without modifying the spec. These fields:

- MUST NOT conflict with NAXS-defined field names.
- MUST be preserved by conforming consumers.
- SHOULD use a vendor prefix to avoid collisions (e.g. `"vendor:optimizer_state"`, `"acme:quantization"`).

### 11.2 Operator Type Registration

New operator types can be proposed for inclusion in the standard registry. The process:

1. Define the type name, description, expected parameters, and input/output arity.
2. Provide at least 3 real-world architecture examples using the type.
3. Submit a PR to the NAXS specification repository.
4. Types are added in the next minor version.

### 11.3 Versioning

NAXS uses semantic versioning:

- **Major** (1.0 → 2.0): Breaking changes to required fields or semantics.
- **Minor** (1.0 → 1.1): New optional fields, new operator types, new standard metadata keys.
- **Patch** (1.0.0 → 1.0.1): Clarifications, documentation fixes, schema corrections.

The `spec_version` field uses major.minor format (e.g. `"0.1"`).

Consumers MUST check `spec_version` and reject only if the major version is higher than supported. Unknown minor version fields MUST be preserved.

---

## 12. Scope Notation

The `scope` field on components provides hierarchical grouping using dot notation:

```
layer.0.attention
layer.0.ffn
encoder.block.1.norm
features.stage.1
backbone.stem
```

### 12.1 Scope Rules

- Scope segments are separated by `.`.
- Numeric segments (e.g. `0`, `1`, `2`) typically indicate layer/block indices.
- Scope is **informational**: it aids grouping, visualization, and analysis but does not define execution order.
- Two components with the same scope belong to the same logical group.
- Components without a scope are in the root group.

### 12.2 Common Scope Patterns

| Pattern | Example | Meaning |
|---------|---------|---------|
| `layer.N.attention` | `layer.0.attention` | Layer N's attention sub-block |
| `layer.N.ffn` | `layer.0.ffn` | Layer N's feed-forward sub-block |
| `layer.N` | `layer.0` | Layer N (composite block) |
| `encoder.layer.N` | `encoder.layer.0` | Encoder's layer N |
| `decoder.layer.N` | `decoder.layer.0` | Decoder's layer N |
| `backbone` | `backbone` | Backbone / feature extractor |
| `head` | `head` | Task-specific head |
| `embeddings` | `embeddings` | Embedding layer group |
| `stem` | `stem` | Initial processing layers |

> See [Appendix C](#appendix-c-scope-pattern-catalog) for the full catalog of observed scope patterns.

---

## 13. Validation Rules

A conforming NAXS document MUST satisfy:

### 13.1 Structural Integrity

1. `spec_version`, `id`, `name`, `components` are present and non-null.
2. `components` is a non-empty array.
3. Every component has `id`, `type`, `name`, `params`, `inputs`, `outputs`.
4. All component `id` values are unique within the document.
5. All `inputs` and `outputs` values reference existing component IDs.
6. If `connections` is present, every connection has `id`, `from`, `to`.
7. All connection `from` and `to` values reference existing component IDs.
8. All connection `id` values are unique within the document.

### 13.2 Consistency

9. For every component A that lists B in its `outputs`, B MUST list A in its `inputs`.
10. For every connection `{ "from": A, "to": B }`, A MUST list B in its `outputs` and B MUST list A in its `inputs`.
11. The graph MAY be acyclic or cyclic. Cyclic graphs (recurrent architectures) are valid.

### 13.3 Parameter Validity

12. `params` is a JSON object (may be empty `{}`).
13. Parameter values are limited to: integer, float, boolean, string, array.
14. Array elements are limited to: integer, string (symbolic dimension).
15. Parameter values MUST NOT be `null`, nested objects, or arrays of arrays.

### 13.4 Soft Validation (Warnings)

The following are not errors but SHOULD be flagged:

- Components with `type: "custom"` and empty `params`.
- Components without a `scope`.
- Parameter names not in the standard registry for the given `type`.
- Documents without a `description`.

> **Validation Checklist for Implementers:**
> - [ ] All required fields present and non-null (rules 1–3, 6)
> - [ ] All IDs unique (rules 4, 8)
> - [ ] All references resolve to existing IDs (rules 5, 7)
> - [ ] `inputs`/`outputs` bidirectional consistency (rules 9–10)
> - [ ] No `null`/nested-object/array-of-array param values (rules 12–15)
> - [ ] Soft warnings reported separately from errors (§13.4)
> - [ ] Block template rules checked (§25.11) if `block_templates` present

---

## 14. Minimal Example

The smallest valid NAXS document:

```json
{
  "spec_version": "0.1",
  "id": "minimal-mlp",
  "name": "Minimal MLP",
  "components": [
    {
      "id": "n1",
      "type": "input",
      "name": "x",
      "params": { "shape": [10] },
      "inputs": [],
      "outputs": ["n2"]
    },
    {
      "id": "n2",
      "type": "linear",
      "name": "fc1",
      "params": { "inFeatures": 10, "outFeatures": 5 },
      "inputs": ["n1"],
      "outputs": []
    }
  ],
  "connections": [
    {
      "id": "c1",
      "from": "n1",
      "to": "n2",
      "fromPort": "bottom",
      "toPort": "top"
    }
  ]
}
```

---

## 15. Full Example: BERT-Base (Excerpt)

```json
{
  "spec_version": "0.1",
  "id": "bert-base",
  "name": "BERT-Base",
  "description": "BERT-Base: 12-layer transformer encoder, hidden size 768, 12 attention heads.",
  "category": "NLP",
  "components": [
    {
      "id": "n1",
      "type": "input",
      "name": "Input",
      "params": { "shape": [1, 512, 768] },
      "inputs": [],
      "outputs": ["n2"],
      "inputShape": [1, 512, 768]
    },
    {
      "id": "n2",
      "type": "embedding",
      "name": "Embedding",
      "params": {
        "vocabSize": 30522,
        "embeddingDim": 768,
        "maxSeqLen": 512
      },
      "inputs": ["n1"],
      "outputs": ["n3", "n4"],
      "scope": "embeddings"
    },
    {
      "id": "n3",
      "type": "multiHeadAttention",
      "name": "Attention_1",
      "params": {
        "numHeads": 12,
        "hiddenDim": 768
      },
      "inputs": ["n2"],
      "outputs": ["n4"],
      "scope": "layer.0.attention"
    },
    {
      "id": "n4",
      "type": "add",
      "name": "Add_1",
      "params": {},
      "inputs": ["n2", "n3"],
      "outputs": ["n5"],
      "scope": "layer.0.attention"
    },
    {
      "id": "n5",
      "type": "layerNorm",
      "name": "LayerNorm_1_1",
      "params": { "normalizedShape": 768 },
      "inputs": ["n4"],
      "outputs": ["n6"],
      "scope": "layer.0.attention"
    },
    {
      "id": "n6",
      "type": "feedForward",
      "name": "FFN_1",
      "params": {
        "hiddenDim": 768,
        "ffDim": 3072
      },
      "inputs": ["n5"],
      "outputs": ["n7", "n8"],
      "scope": "layer.0.ffn"
    }
  ],
  "connections": [
    { "id": "c1", "from": "n1", "to": "n2", "fromPort": "bottom", "toPort": "top" },
    { "id": "c2", "from": "n2", "to": "n3", "fromPort": "bottom", "toPort": "top" },
    { "id": "c3", "from": "n2", "to": "n4", "fromPort": "bottom", "toPort": "top" },
    { "id": "c4", "from": "n3", "to": "n4", "fromPort": "bottom", "toPort": "top" },
    { "id": "c5", "from": "n4", "to": "n5", "fromPort": "bottom", "toPort": "top" },
    { "id": "c6", "from": "n5", "to": "n6", "fromPort": "bottom", "toPort": "top" }
  ],
  "metadata": {
    "framework": "pytorch",
    "paper": "https://arxiv.org/abs/1810.04805",
    "checkpoint": "https://huggingface.co/bert-base-uncased",
    "license": "apache-2.0"
  },
  "provenance": {
    "source": "atlas/architectures/bert-base/model.json",
    "original_format": "atlas-model-json",
    "imported_by": "manual"
  }
}
```

---

## 16. Full Example: ResNet-50 (Excerpt)

```json
{
  "spec_version": "0.1",
  "id": "resnet-50",
  "name": "ResNet-50",
  "description": "ResNet-50: deep residual CNN with 50 layers, bottleneck blocks.",
  "category": "Computer Vision",
  "components": [
    {
      "id": "n1",
      "type": "input",
      "name": "image",
      "params": { "shape": [3, 224, 224] },
      "inputs": [],
      "outputs": ["n2"]
    },
    {
      "id": "n2",
      "type": "conv2d",
      "name": "conv1 7x7/2",
      "params": {
        "inChannels": 3,
        "outChannels": 64,
        "kernelSize": 7,
        "stride": 2,
        "padding": 3
      },
      "inputs": ["n1"],
      "outputs": ["n3"],
      "scope": "stem"
    },
    {
      "id": "n3",
      "type": "batchNorm",
      "name": "bn1",
      "params": { "numFeatures": 64 },
      "inputs": ["n2"],
      "outputs": ["n4"],
      "scope": "stem"
    },
    {
      "id": "n4",
      "type": "relu",
      "name": "relu1",
      "params": {},
      "inputs": ["n3"],
      "outputs": ["n5"],
      "scope": "stem"
    }
  ],
  "connections": [
    { "id": "c1", "from": "n1", "to": "n2", "fromPort": "bottom", "toPort": "top" },
    { "id": "c2", "from": "n2", "to": "n3", "fromPort": "bottom", "toPort": "top" },
    { "id": "c3", "from": "n3", "to": "n4", "fromPort": "bottom", "toPort": "top" }
  ]
}
```

---

## 17. Full Example: Llama-3-8B (Excerpt)

```json
{
  "spec_version": "0.1",
  "id": "llama3-8b",
  "name": "Llama-3-8B",
  "description": "Llama-3-8B: 32-layer decoder-only transformer with GQA, RoPE, SwiGLU FFN.",
  "category": "NLP",
  "components": [
    {
      "id": "n1",
      "type": "input",
      "name": "Input",
      "params": { "shape": [1, 8192, 4096] },
      "inputs": [],
      "outputs": ["n2"],
      "inputShape": [1, 8192, 4096]
    },
    {
      "id": "n2",
      "type": "embedding",
      "name": "Embedding",
      "params": {
        "vocabSize": 128256,
        "embeddingDim": 4096,
        "maxSeqLen": 8192
      },
      "inputs": ["n1"],
      "outputs": ["n3", "n5"],
      "scope": "embeddings"
    },
    {
      "id": "n3",
      "type": "rmsNorm",
      "name": "RMSNorm_1_1",
      "params": { "normalizedShape": 4096 },
      "inputs": ["n2"],
      "outputs": ["n4"]
    },
    {
      "id": "n4",
      "type": "groupedQueryAttention",
      "name": "Attention_1",
      "params": {
        "embedDim": 4096,
        "numHeads": 32,
        "numKVHeads": 8,
        "headDim": 128
      },
      "inputs": ["n3"],
      "outputs": ["n5"],
      "scope": "layer.0.attention"
    }
  ],
  "connections": [
    { "id": "c1", "from": "n1", "to": "n2", "fromPort": "bottom", "toPort": "top" },
    { "id": "c2", "from": "n2", "to": "n3", "fromPort": "bottom", "toPort": "top" },
    { "id": "c3", "from": "n3", "to": "n4", "fromPort": "bottom", "toPort": "top" }
  ]
}
```

---

## 18. Full Example: Mamba SSM Block (Excerpt)

Demonstrates non-transformer architecture with SSM, conv1d, and gating:

```json
{
  "spec_version": "0.1",
  "id": "mamba-block",
  "name": "Mamba SSM Block",
  "description": "Mamba State Space Model block — selective SSM with causal conv + gating.",
  "components": [
    {
      "id": "input_tokens",
      "type": "input",
      "name": "tokens",
      "params": { "shape": [1, 1024] },
      "inputs": [],
      "outputs": ["embed"]
    },
    {
      "id": "embed",
      "type": "embedding",
      "name": "embed",
      "scope": "embeddings",
      "params": {
        "numEmbeddings": 50280,
        "embeddingDim": 1024
      },
      "inputs": ["input_tokens"],
      "outputs": ["norm1", "residual1"],
      "notes": "Token embedding D=1024 (Mamba-1.4B dim)"
    },
    {
      "id": "norm1",
      "type": "rmsNorm",
      "name": "norm_ssm",
      "scope": "layer.0.ssm",
      "params": { "normalizedShape": 1024 },
      "inputs": ["embed"],
      "outputs": ["in_proj"],
      "notes": "Pre-SSM RMSNorm"
    },
    {
      "id": "in_proj",
      "type": "linear",
      "name": "in_proj",
      "scope": "layer.0.ssm",
      "params": {
        "outFeatures": 4096,
        "inFeatures": 1024
      },
      "inputs": ["norm1"],
      "outputs": ["causal_conv", "z_gate"],
      "notes": "Projects to 2x expand (4096) — split into x and z branches"
    },
    {
      "id": "causal_conv",
      "type": "conv1d",
      "name": "causal_conv",
      "scope": "layer.0.ssm",
      "params": {
        "outChannels": 2048,
        "kernelSize": 4,
        "stride": 1,
        "padding": 3,
        "inChannels": 4096
      },
      "inputs": ["in_proj"],
      "outputs": ["silu_x"]
    },
    {
      "id": "silu_x",
      "type": "swish",
      "name": "silu_x",
      "scope": "layer.0.ssm",
      "params": {},
      "inputs": ["causal_conv"],
      "outputs": ["ssm_proj"]
    },
    {
      "id": "z_gate",
      "type": "swish",
      "name": "z_gate",
      "scope": "layer.0.ssm",
      "params": {},
      "inputs": ["in_proj"],
      "outputs": ["gate_multiply"]
    },
    {
      "id": "gate_multiply",
      "type": "multiply",
      "name": "gate_out",
      "scope": "layer.0.ssm",
      "params": {},
      "inputs": ["ssm_proj", "z_gate"],
      "outputs": ["out_proj"],
      "notes": "Element-wise gate: SSM(x) ⊙ z"
    }
  ],
  "connections": [
    { "id": "c1", "from": "input_tokens", "to": "embed" },
    { "id": "c2", "from": "embed", "to": "norm1" },
    { "id": "c3", "from": "norm1", "to": "in_proj" },
    { "id": "c4", "from": "in_proj", "to": "causal_conv" },
    { "id": "c5", "from": "in_proj", "to": "z_gate" },
    { "id": "c6", "from": "causal_conv", "to": "silu_x" },
    { "id": "c7", "from": "silu_x", "to": "ssm_proj" },
    { "id": "c8", "from": "z_gate", "to": "gate_multiply" },
    { "id": "c9", "from": "ssm_proj", "to": "gate_multiply" }
  ]
}
```

---

## 19. Full Example: 3D Gaussian Splatting (Custom Operators)

Demonstrates a non-neural-network architecture using `custom` operator types:

```json
{
  "spec_version": "0.1",
  "id": "3dgs",
  "name": "3D Gaussian Splatting",
  "description": "Real-time radiance field rendering with 3D Gaussians and tile-based splatting.",
  "category": "3D Rendering",
  "components": [
    {
      "id": "n1",
      "type": "input",
      "name": "SfM Sparse Point Cloud plus Calibrated Cameras",
      "params": {},
      "inputs": [],
      "outputs": ["n2"]
    },
    {
      "id": "n2",
      "type": "custom",
      "name": "3D Gaussian Initialization (position, opacity, anisotropic covariance, SH)",
      "params": {},
      "inputs": ["n1"],
      "outputs": ["n3"],
      "scope": "representation"
    },
    {
      "id": "n3",
      "type": "custom",
      "name": "Interleaved Optimization and Adaptive Density Control",
      "params": {},
      "inputs": ["n2"],
      "outputs": ["n4"],
      "scope": "optimization"
    },
    {
      "id": "n4",
      "type": "custom",
      "name": "Visibility-Aware Tile-Based Splatting Rasterizer",
      "params": {},
      "inputs": ["n3"],
      "outputs": ["n5"],
      "scope": "renderer"
    },
    {
      "id": "n5",
      "type": "output",
      "name": "Rendered Image",
      "params": {},
      "inputs": ["n4"],
      "outputs": []
    }
  ],
  "connections": [
    { "id": "c1", "from": "n1", "to": "n2" },
    { "id": "c2", "from": "n2", "to": "n3" },
    { "id": "c3", "from": "n3", "to": "n4" },
    { "id": "c4", "from": "n4", "to": "n5" }
  ]
}
```

---

## 20. Conformance

### 20.1 Producer Conformance

A **producer** is conforming if it generates documents that:

1. Are valid JSON.
2. Include all required top-level fields (`spec_version`, `id`, `name`, `components`, `connections`).
3. Include all required component fields (`id`, `type`, `name`, `params`, `inputs`, `outputs`).
4. Include all required connection fields (`id`, `from`, `to`).
5. Satisfy all validation rules in [§13](#13-validation-rules).
6. Set `spec_version` to a valid version string.

### 20.2 Consumer Conformance

A **consumer** is conforming if it:

1. Parses any valid NAXS document without error.
2. Preserves all unknown fields (top-level, component, connection) through read/write cycles.
3. Constructs a directed graph from `components` and `connections`.
4. Does not fail when encountering unknown operator types (treats them as opaque).
5. Does not fail when encountering unknown parameter names.
6. Checks `spec_version` and warns (but does not fail) on unknown minor versions.
7. Rejects only on major version mismatch or structural validation failure ([§13.1](#131-structural-integrity)).

### 20.3 Validator Conformance

A **validator** is conforming if it:

1. Checks all rules in [§13](#13-validation-rules).
2. Reports errors with field paths and human-readable messages.
3. Reports soft validation warnings ([§13.4](#134-soft-validation-warnings)) separately from errors.
4. Can validate both individual documents and batch (directory) inputs.

---

## 21. JSON Schema

A machine-readable JSON Schema is provided alongside this specification at:

```
naxs/v0.1/schema.json
```

The schema defines:
- Required and optional fields at each level.
- Parameter value type constraints.
- Component ID uniqueness (via `uniqueItemsProperties`).
- Reference integrity (via `$ref` validation in application code, not JSON Schema).

The JSON Schema is normative for structural validation. This document is normative for semantic validation.

---

## 22. Migration from Atlas `model.json`

The NAXS 0.1 format is a superset of the existing Atlas `model.json` format. Migration is straightforward:

| Atlas `model.json` | NAXS 0.1 | Action |
|---------------------|----------|--------|
| `id` | `id` | Unchanged |
| `name` | `name` | Unchanged |
| `description` | `description` | Unchanged (optional in both) |
| `components` | `components` | Unchanged |
| `connections` | `connections` | Unchanged |
| (none) | `spec_version` | **Add** `"0.1"` |
| `realParamCount` | `real_param_count` | Rename (snake_case) |
| `icon` | `icon` | Unchanged |
| `category` | `category` | Unchanged |
| (none) | `metadata` | **Optional**: add framework, paper, checkpoint |
| (none) | `provenance` | **Optional**: add source, import info |

Component fields (`id`, `type`, `name`, `params`, `inputs`, `outputs`, `scope`, `position`, `inputShape`, `notes`) are unchanged.

Connection fields (`id`, `from`, `to`, `fromPort`, `toPort`) are unchanged.

**Migration is additive only** — no existing field is removed or renamed (except `realParamCount` → `real_param_count`). A `model.json` file with `spec_version: "0.1"` added is a valid NAXS document.

---

## 23. Glossary

| Term | Definition |
|------|-----------|
| **Architecture** | A complete neural network topology, represented as a directed graph of components and connections. |
| **Component** | A single node in the architecture graph; an instance of an operator type with concrete parameters. |
| **Connection** | A directed edge between two components, indicating data flow. |
| **Operator Type** | A named category of computation (e.g. `conv2d`, `multiHeadAttention`). |
| **Parameter** | A configurable property of a component (e.g. `numHeads`, `kernelSize`). |
| **Scope** | A dot-separated hierarchical path grouping components (e.g. `layer.0.attention`). |
| **Port** | A named connection point on a component. NAXS 0.1 uses visual port labels; semantic ports are reserved for future versions. |
| **Block** | A reusable sub-graph with an explicit interface. NAXS defines block templates ([§25](#25-block-templates-and-repetition)) that can be referenced and repeated. Blocks can also be represented as architectures with scoped components. |
| **Provenance** | Information about how a document was created or transformed. |
| **Metadata** | Vendor-specific information that does not affect architectural semantics. |

---

## 24. Change Log

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-09-23 | Initial public draft. Includes block templates ([§25](#25-block-templates-and-repetition)): reusable subgraph definitions, `block_ref` components, `repeat` directives for layer/block repetition, parameter binding, and scope index substitution. |

---

## 25. Block Templates and Repetition

NAXS requires every component to be listed individually — a 12-layer transformer has 48+ explicit component objects even though all 12 layers are structurally identical. This section introduces **block templates** and **repetition directives** that allow a single template definition to generate many concrete components, dramatically reducing document size and enabling true architectural reuse.

### 25.1 The Problem

Empirical analysis of the Atlas knowledge base (288 architectures, 9,735 components) reveals massive redundancy:

| Architecture | Components | Unique Layer Patterns | Redundancy |
|--------------|-----------|----------------------|------------|
| BERT-Base | 51 | 1 (×12 layers) | 92% |
| Llama-4-Scout | 434 | ~3 (×32 layers) | 87% |
| DeepSeek-v3 | 371 | ~4 (×61 layers) | 84% |
| ResNet-50 | 176 | ~4 (×16 blocks) | 75% |

Without a repetition mechanism, every layer is fully expanded, making documents verbose, error-prone, and difficult to modify (changing `hiddenDim` requires editing 12 copies).

### 25.2 Block Template Definition

A **block template** is a named, parameterized subgraph definition stored in the top-level `block_templates` array. It defines:

- A unique `id` for reference
- A `params` schema listing the template's parameters
- A `nodes` array of component prototypes (the subgraph topology)
- An `edges` array of internal connections
- An `interface` declaring external input/output ports

```json
{
  "block_templates": [
    {
      "id": "transformer_encoder_layer",
      "description": "Standard transformer encoder layer: attention + residual + LayerNorm + FFN + residual + LayerNorm",
      "params": {
        "hiddenDim": { "type": "integer", "description": "Hidden dimension size" },
        "numHeads": { "type": "integer", "description": "Number of attention heads" },
        "ffDim": { "type": "integer", "description": "Feed-forward intermediate dimension" }
      },
      "nodes": [
        {
          "id": "attn",
          "type": "multiHeadAttention",
          "name": "Attention",
          "params": {
            "numHeads": "$numHeads",
            "hiddenDim": "$hiddenDim"
          }
        },
        {
          "id": "add1",
          "type": "add",
          "name": "ResidualAdd1",
          "params": {}
        },
        {
          "id": "ln1",
          "type": "layerNorm",
          "name": "LayerNorm1",
          "params": { "normalizedShape": "$hiddenDim" }
        },
        {
          "id": "ffn",
          "type": "feedForward",
          "name": "FFN",
          "params": {
            "hiddenDim": "$hiddenDim",
            "ffDim": "$ffDim"
          }
        },
        {
          "id": "add2",
          "type": "add",
          "name": "ResidualAdd2",
          "params": {}
        },
        {
          "id": "ln2",
          "type": "layerNorm",
          "name": "LayerNorm2",
          "params": { "normalizedShape": "$hiddenDim" }
        }
      ],
      "edges": [
        { "from": "attn", "to": "add1" },
        { "from": "add1", "to": "ln1" },
        { "from": "ln1", "to": "ffn" },
        { "from": "ffn", "to": "add2" },
        { "from": "add2", "to": "ln2" }
      ],
      "interface": {
        "inputs": [
          { "name": "x", "description": "Input tensor [batch, seq, hiddenDim]" }
        ],
        "outputs": [
          { "name": "y", "source_node": "ln2", "description": "Output tensor [batch, seq, hiddenDim]" }
        ]
      }
    }
  ]
}
```

> **For Implementers:** A block template's `nodes` are **prototypes** — they are not real components in the document graph. They only become real components when a `block_ref` component references and expands them. Think of templates as functions and `block_ref` components as function calls.

### 25.3 Block Reference Components

A component can reference a block template using the `block_ref` field. When a consumer encounters a `block_ref` component, it **expands** the referenced template: the template's nodes are instantiated and inserted into the document's component graph, replacing the reference component.

```json
{
  "id": "layer_0",
  "type": "block",
  "name": "TransformerLayer_0",
  "block_ref": "transformer_encoder_layer",
  "params": {
    "hiddenDim": 768,
    "numHeads": 12,
    "ffDim": 3072
  },
  "inputs": ["embed_out"],
  "outputs": ["layer_1"]
}
```

**Expansion semantics:**

1. The consumer looks up `block_ref` in the document's `block_templates` array.
2. Template parameters (declared in `params`) are bound to the values in the component's `params`.
3. Each template node is instantiated with a **prefixed ID**: `{component_id}.{node_id}` (e.g. `layer_0.attn`).
4. Parameter references (`$paramName`) in template node params are replaced with bound values.
5. Template edges are instantiated between prefixed node IDs.
6. The component's `inputs` connect to the template's first interface input; the template's interface output connects to the component's `outputs`.
7. The expanded nodes inherit the component's `scope` (if set), with the template node's local scope appended.

**A `block_ref` component is semantically equivalent to its expansion.** A document with block references and a document with the same components fully expanded produce identical architecture graphs. Consumers MAY expand block references eagerly (at load time) or lazily (on demand).

### 25.4 Repeat Directive

The `repeat` field on a component instructs the consumer to instantiate the component N times, creating a chain of repeated blocks. This is the primary mechanism for representing stacked layers (transformer layers, ResNet stages, etc.).

```json
{
  "id": "layers",
  "type": "block",
  "name": "TransformerLayers",
  "block_ref": "transformer_encoder_layer",
  "params": {
    "hiddenDim": 768,
    "numHeads": 12,
    "ffDim": 3072
  },
  "repeat": {
    "count": 12,
    "mode": "sequential"
  },
  "inputs": ["embed_out"],
  "outputs": ["ln_final"]
}
```

**Repeat modes:**

| Mode | Description | Inter-layer Connection |
|------|-------------|----------------------|
| `sequential` | Instances are chained: output of instance *i* feeds into input of instance *i+1*. | Automatic: `instance[i].output → instance[i+1].input` |
| `parallel` | All instances share the same input; outputs are collected (e.g. multi-head ensemble). | Automatic: `input → all instances`; all instance outputs → output node |
| `stacked` | Instances are independent; the caller wires connections explicitly. | Manual: caller provides connections referencing expanded IDs |

**Expanded ID scheme for repeated components:**

For a component with `id: "layers"` and `repeat: { count: 3 }`:

| Instance | Expanded ID | Scope (if component scope is `encoder`) |
|----------|-------------|----------------------------------------|
| 0 | `layers.0` | `encoder.layer.0` |
| 1 | `layers.1` | `encoder.layer.1` |
| 2 | `layers.2` | `encoder.layer.2` |

Each instance's internal nodes are further prefixed: `layers.0.attn`, `layers.1.attn`, etc.

**Scope index substitution:** When a repeated component has a `scope` field containing `$i`, the index variable is substituted:

```json
{
  "scope": "encoder.layer.$i",
  "repeat": { "count": 12, "mode": "sequential" }
}
```

This produces scopes `encoder.layer.0`, `encoder.layer.1`, ..., `encoder.layer.11`.

### 25.5 Parameter Binding

Template node parameters use **`$`-prefixed references** to bind to template-level parameters:

| Syntax | Meaning | Example |
|--------|---------|---------|
| `$paramName` | Reference to a template parameter | `"$hiddenDim"` → `768` |
| `$i` | Current repetition index (0-based) | `"$i"` → `0`, `1`, ..., `11` |
| `{$expr: "..."}` | Arithmetic expression over parameters | `{"$expr": "hiddenDim * 4"}` → `3072` |
| Literal value | Passed through unchanged | `768`, `"gelu"`, `true` |

**Expression syntax** supports `+`, `-`, `*`, `/`, parentheses, and parameter references (without `$`):

```json
{
  "params": {
    "ffDim": { "$expr": "hiddenDim * 4" },
    "headDim": { "$expr": "hiddenDim / numHeads" }
  }
}
```

This allows derived parameters to be computed from base parameters without duplicating values.

### 25.6 Per-Instance Parameter Overrides

Individual repetition instances can override template parameters. The `repeat.overrides` array provides per-instance parameter values:

```json
{
  "repeat": {
    "count": 4,
    "mode": "sequential",
    "overrides": [
      { "index": 0, "params": { "numHeads": 8 } },
      { "index": 3, "params": { "numHeads": 16 } }
    ]
  }
}
```

Instances not listed in `overrides` use the base `params`. This handles architectures where layer parameters vary across layers (e.g. growing attention heads, changing FFN dimensions).

### 25.7 Nested Block Templates

Block templates can reference other block templates, enabling hierarchical composition:

```json
{
  "block_templates": [
    {
      "id": "transformer_stage",
      "params": {
        "numLayers": { "type": "integer" },
        "hiddenDim": { "type": "integer" },
        "numHeads": { "type": "integer" },
        "ffDim": { "type": "integer" }
      },
      "nodes": [
        {
          "id": "layers",
          "type": "block",
          "block_ref": "transformer_encoder_layer",
          "params": {
            "hiddenDim": "$hiddenDim",
            "numHeads": "$numHeads",
            "ffDim": "$ffDim"
          },
          "repeat": {
            "count": "$numLayers",
            "mode": "sequential"
          }
        }
      ],
      "edges": [],
      "interface": {
        "inputs": [{ "name": "x" }],
        "outputs": [{ "name": "y", "source_node": "layers" }]
      }
    }
  ]
}
```

Nesting depth is not limited by the spec. Consumers SHOULD detect and report circular block references.

### 25.8 Complete Example: BERT-Base with Repetition

The following NAXS document represents BERT-Base (12 transformer layers) using a single block template and a repeat directive — **5 components instead of 51**:

```json
{
  "spec_version": "0.1",
  "id": "bert-base",
  "name": "BERT-Base",
  "description": "BERT-Base: 12-layer transformer encoder, hidden size 768, 12 attention heads.",
  "block_templates": [
    {
      "id": "transformer_encoder_layer",
      "description": "Standard transformer encoder layer",
      "params": {
        "hiddenDim": { "type": "integer" },
        "numHeads": { "type": "integer" },
        "ffDim": { "type": "integer" }
      },
      "nodes": [
        { "id": "attn", "type": "multiHeadAttention", "name": "Attention", "params": { "numHeads": "$numHeads", "hiddenDim": "$hiddenDim" } },
        { "id": "add1", "type": "add", "name": "ResidualAdd1", "params": {} },
        { "id": "ln1", "type": "layerNorm", "name": "LayerNorm1", "params": { "normalizedShape": "$hiddenDim" } },
        { "id": "ffn", "type": "feedForward", "name": "FFN", "params": { "hiddenDim": "$hiddenDim", "ffDim": "$ffDim" } },
        { "id": "add2", "type": "add", "name": "ResidualAdd2", "params": {} },
        { "id": "ln2", "type": "layerNorm", "name": "LayerNorm2", "params": { "normalizedShape": "$hiddenDim" } }
      ],
      "edges": [
        { "from": "attn", "to": "add1" },
        { "from": "add1", "to": "ln1" },
        { "from": "ln1", "to": "ffn" },
        { "from": "ffn", "to": "add2" },
        { "from": "add2", "to": "ln2" }
      ],
      "interface": {
        "inputs": [{ "name": "x" }],
        "outputs": [{ "name": "y", "source_node": "ln2" }]
      }
    }
  ],
  "components": [
    {
      "id": "input",
      "type": "input",
      "name": "Input",
      "params": { "shape": [1, 512, 768] },
      "inputs": [],
      "outputs": ["embed"]
    },
    {
      "id": "embed",
      "type": "embedding",
      "name": "Embedding",
      "params": { "vocabSize": 30522, "embeddingDim": 768, "maxSeqLen": 512 },
      "inputs": ["input"],
      "outputs": ["layers"],
      "scope": "embeddings"
    },
    {
      "id": "layers",
      "type": "block",
      "name": "TransformerLayers",
      "block_ref": "transformer_encoder_layer",
      "params": { "hiddenDim": 768, "numHeads": 12, "ffDim": 3072 },
      "repeat": { "count": 12, "mode": "sequential" },
      "inputs": ["embed"],
      "outputs": ["ln_f"],
      "scope": "encoder.layer.$i"
    },
    {
      "id": "ln_f",
      "type": "layerNorm",
      "name": "FinalLayerNorm",
      "params": { "normalizedShape": 768 },
      "inputs": ["layers"],
      "outputs": ["output"],
      "scope": "encoder"
    },
    {
      "id": "output",
      "type": "output",
      "name": "Output",
      "params": {},
      "inputs": ["ln_f"],
      "outputs": []
    }
  ],
  "connections": [
    { "id": "c1", "from": "input", "to": "embed" },
    { "id": "c2", "from": "embed", "to": "layers" },
    { "id": "c3", "from": "layers", "to": "ln_f" },
    { "id": "c4", "from": "ln_f", "to": "output" }
  ]
}
```

**Expansion result:** This 5-component document expands to the same 51-component graph as the NAXS BERT-Base example ([§15](#15-full-example-bert-base-excerpt)). The expansion is:

| Component | Expands To |
|-----------|-----------|
| `layers` (repeat: 12) | `layers.0` through `layers.11`, each containing 6 nodes (`attn`, `add1`, `ln1`, `ffn`, `add2`, `ln2`) |
| Total expanded components | 51 (same as §15) |
| Total expanded connections | 62 (same as §15) |

### 25.9 Expansion Algorithm

A conforming consumer MUST implement the following expansion algorithm:

```
function expand_document(doc):
    templates = { t.id: t for t in doc.block_templates }
    expanded_components = []
    expanded_connections = []

    for component in doc.components:
        if component has "block_ref" and component has "repeat":
            expanded = expand_repeated_block(component, templates)
        elif component has "block_ref":
            expanded = expand_single_block(component, templates)
        else:
            expanded = [component]  # pass-through

        expanded_components.extend(expanded.nodes)
        expanded_connections.extend(expanded.edges)

    return Document(components=expanded_components, connections=expanded_connections)


function expand_repeated_block(component, templates):
    template = templates[component.block_ref]
    instances = []

    for i in range(component.repeat.count):
        # Merge base params with per-instance overrides
        params = component.params.copy()
        for override in component.repeat.get("overrides", []):
            if override.index == i:
                params.update(override.params)

        # Create instance with prefixed IDs
        instance_prefix = f"{component.id}.{i}"
        scope = substitute_index(component.scope, i)

        nodes = []
        for node in template.nodes:
            expanded_node = {
                "id": f"{instance_prefix}.{node.id}",
                "type": node.type,
                "name": f"{node.name}_{i}",
                "params": resolve_params(node.params, params, i),
                "scope": f"{scope}.{node.id}" if scope else node.id
            }
            nodes.append(expanded_node)

        # Internal edges
        edges = []
        for edge in template.edges:
            edges.append({
                "from": f"{instance_prefix}.{edge.from}",
                "to": f"{instance_prefix}.{edge.to}"
            })

        # Inter-instance connections (sequential mode)
        if i > 0 and component.repeat.mode == "sequential":
            prev_output = get_interface_output(instances[-1], template)
            curr_input = get_interface_input(nodes[0], template)
            edges.append({ "from": prev_output, "to": curr_input })

        instances.append(Instance(nodes, edges))

    # Connect first instance input to component inputs
    # Connect last instance output to component outputs
    return merge_instances(instances, component)


function resolve_params(node_params, bound_params, index):
    result = {}
    for key, value in node_params:
        if value is string and starts with "$":
            param_name = value[1:]
            if param_name == "i":
                result[key] = index
            else:
                result[key] = bound_params[param_name]
        elif value is object and has "$expr":
            result[key] = eval_expr(value["$expr"], bound_params)
        else:
            result[key] = value  # literal
    return result
```

### 25.10 Backward Compatibility

Block templates are fully backward compatible:

1. **Documents without `block_templates`, `block_ref`, or `repeat`** are processed identically — the expansion algorithm is a no-op pass-through.
2. **A document with block templates expands to standard components and connections** — no `block_ref` or `repeat` fields remain after expansion.
3. **Consumers SHOULD expand block references before graph analysis.** A consumer MAY choose to work with the unexpanded form for certain operations (e.g. counting layers, comparing architectures structurally).

### 25.11 Validation Rules for Block Templates

In addition to the rules in [§13](#13-validation-rules), documents with block templates MUST satisfy:

1. Every `block_templates` entry has a unique `id`.
2. Every `block_ref` value references an existing template `id`.
3. Template `nodes` have unique `id` values within the template.
4. Template `edges` reference existing node `id` values within the template.
5. `repeat.count` is a positive integer (≥ 1).
6. `repeat.mode` is one of `"sequential"`, `"parallel"`, `"stacked"`.
7. Per-instance `overrides` indices are within `[0, count-1]`.
8. No circular block references (template A references template B which references template A).
9. All `$paramName` references in template nodes resolve to declared template parameters or the reserved `$i`.
10. `{$expr: "..."}` expressions are syntactically valid and reference declared parameters.

> **Block Template Validation Checklist for Implementers:**
> - [ ] Template IDs unique (rule 1)
> - [ ] All `block_ref` values resolve (rule 2)
> - [ ] Node IDs unique within each template (rule 3)
> - [ ] Edge `from`/`to` reference valid template nodes (rule 4)
> - [ ] `repeat.count` ≥ 1 (rule 5)
> - [ ] `repeat.mode` is valid enum value (rule 6)
> - [ ] Override indices in range (rule 7)
> - [ ] No circular references — detect via DFS/traversal (rule 8)
> - [ ] All `$paramName` resolve to declared params or `$i` (rule 9)
> - [ ] `$expr` expressions parse and reference valid params (rule 10)
> - [ ] Post-expansion graph has no dangling refs or duplicate IDs

### 25.12 Conformance Updates

**Producer Conformance** (extends [§20.1](#201-producer-conformance)):

- A producer MAY emit `block_templates`, `block_ref`, and `repeat` fields.
- A producer that emits block templates MUST ensure they expand to valid standard components.
- A producer SHOULD use block templates for any architecture with ≥ 3 structurally identical repeated layers.

**Consumer Conformance** (extends [§20.2](#202-consumer-conformance)):

- A consumer MUST recognize `block_templates`, `block_ref`, and `repeat` fields.
- A consumer MUST expand block references when constructing the architecture graph.
- A consumer MAY provide both expanded and unexpanded views.

**Validator Conformance** (extends [§20.3](#203-validator-conformance)):

- A validator MUST check all rules in [§25.11](#2511-validation-rules-for-block-templates).
- A validator SHOULD verify that expansion produces a valid graph (no dangling references, no duplicate IDs after expansion).

---

## Appendix A: Standard Parameter Name Catalog

The following parameter names appear across the 288 architectures in the Atlas knowledge base. They are **recommended** (not required) for the indicated operator types.

### Attention Parameters

| Parameter | Type | Used By | Example |
|-----------|------|---------|---------|
| `numHeads` | integer | `multiHeadAttention`, `groupedQueryAttention`, `transformerBlock` | `12` |
| `hiddenDim` | integer | `multiHeadAttention`, `feedForward` | `768` |
| `embedDim` | integer | `groupedQueryAttention` | `4096` |
| `numKVHeads` | integer | `groupedQueryAttention` | `8` |
| `headDim` | integer | `groupedQueryAttention` | `128` |
| `kvLatentDim` | integer | `mla` | `512` |
| `qLatentDim` | integer | `mla` | `512` |
| `ropeHeadDim` | integer | `mla` | `64` |

### Convolution Parameters

| Parameter | Type | Used By | Example |
|-----------|------|---------|---------|
| `inChannels` | integer | `conv2d`, `depthwiseConv2d`, `conv1d` | `3` |
| `outChannels` | integer | `conv2d`, `depthwiseConv2d`, `conv1d` | `64` |
| `kernelSize` | integer or array | `conv2d`, `depthwiseConv2d`, `conv1d` | `7` or `[3, 3]` |
| `stride` | integer or array | `conv2d`, `depthwiseConv2d` | `2` |
| `padding` | integer or array | `conv2d`, `depthwiseConv2d` | `3` |

### Linear Parameters

| Parameter | Type | Used By | Example |
|-----------|------|---------|---------|
| `inFeatures` | integer | `linear` | `1024` |
| `outFeatures` | integer | `linear` | `4096` |
| `bias` | boolean | `linear` | `true` |

### Embedding Parameters

| Parameter | Type | Used By | Example |
|-----------|------|---------|---------|
| `vocabSize` | integer | `embedding` | `30522` |
| `embeddingDim` | integer | `embedding` | `768` |
| `maxSeqLen` | integer | `embedding` | `512` |
| `numEmbeddings` | integer | `embedding` | `50280` |

### Normalization Parameters

| Parameter | Type | Used By | Example |
|-----------|------|---------|---------|
| `normalizedShape` | integer | `layerNorm`, `rmsNorm` | `768` |
| `numFeatures` | integer | `batchNorm` | `64` |

### Feed-Forward Parameters

| Parameter | Type | Used By | Example |
|-----------|------|---------|---------|
| `ffDim` | integer | `feedForward` | `3072` |
| `intermediateSize` | integer | `swiglu`, `geglu` | `11008` |
| `dim` | integer | `swiglu`, `geglu` | `4096` |

### MoE Parameters

| Parameter | Type | Used By | Example |
|-----------|------|---------|---------|
| `numExperts` | integer | `moeLayer`, `sharedExpertMoE` | `256` |
| `expertDim` | integer | `moeLayer`, `sharedExpertMoE` | `7168` |
| `topK` | integer | `moeLayer`, `sharedExpertMoE` | `8` |
| `numSharedExperts` | integer | `sharedExpertMoE` | `1` |

### Patch Embedding Parameters

| Parameter | Type | Used By | Example |
|-----------|------|---------|---------|
| `imgSize` | integer | `patchEmbed` | `224` |
| `patchSize` | integer | `patchEmbed` | `32` |
| `embedDim` | integer | `patchEmbed` | `768` |
| `inChans` | integer | `patchEmbed` | `3` |

### Squeeze-Excitation Parameters

| Parameter | Type | Used By | Example |
|-----------|------|---------|---------|
| `channels` | integer | `seBlock` | `32` |
| `reduction` | integer | `seBlock` | `4` |

### Input Parameters

| Parameter | Type | Used By | Example |
|-----------|------|---------|---------|
| `shape` | array | `input` | `[1, 512, 768]` or `[3, 224, 224]` |

---

## Appendix B: Operator Type Frequency

Based on analysis of 288 architectures (9,735 total components):

| Type | Count | Category |
|------|-------|----------|
| `add` | 2228 | Structural |
| `rmsNorm` | 1820 | Normalization |
| `groupedQueryAttention` | 894 | Attention |
| `swiglu` | 448 | Feed-Forward |
| `custom` | 407 | Core/IO |
| `conv2d` | 393 | Convolution |
| `layerNorm` | 383 | Normalization |
| `feedForward` | 312 | Feed-Forward |
| `input` | 309 | Core/IO |
| `output` | 291 | Core/IO |
| `relu` | 237 | Activation |
| `multiHeadAttention` | 232 | Attention |
| `linear` | 200 | Linear |
| `sharedExpertMoE` | 188 | Specialized |
| `moeLayer` | 173 | Specialized |
| `transformerBlock` | 139 | Structural |
| `batchNorm` | 127 | Normalization |
| `attention` | 97 | Attention |
| `embedding` | 79 | Linear |
| `concatenate` | 75 | Structural |

**Total distinct operator types observed:** 79

---

## Appendix C: Scope Pattern Catalog

Common scope patterns observed across the knowledge base:

| Pattern | Occurrences | Meaning |
|---------|-------------|---------|
| `layer.N.attention` | 1283 | Attention sub-block within layer N |
| `layer.N.ffn` | 710 | Feed-forward sub-block within layer N |
| `layer.N` | 368 | Layer N (composite block) |
| `block` | 116 | Generic block grouping |
| `backbone` | 109 | Feature extraction backbone |
| `encoder` | 78 | Encoder section |
| `decoder` | 48 | Decoder section |
| `head` | 44 | Task-specific output head |
| `heads` | 44 | Multiple output heads |
| `embeddings` | 39 | Embedding layer group |
| `training` | 39 | Training-related components |
| `features.stage.N` | 31 | Feature pyramid stage N |
| `encoder.layer.N.attention` | 30 | Encoder layer N attention |
| `mlp` | 27 | MLP sub-block |

---

## Appendix D: Implementation Notes

### D.1 JSON Parsing

NAXS documents are standard JSON. Any JSON parser can consume them. No custom parser is required.

Key implementation considerations:
- Use a JSON parser that preserves unknown fields (e.g. serde's `#[serde(flatten)]` in Rust, `**kwargs` in Python).
- Parameter values are heterogeneous (`int`, `float`, `bool`, `string`, `array`). Use a tagged union or `JsonValue` type.
- `position` is always `{ "x": number, "y": number }`. Treat as `f64` for maximum precision.

### D.2 Graph Construction

To construct a directed graph from a NAXS document:

1. Create a node for each component, keyed by `id`.
2. For each connection, create a directed edge from `from` to `to`.
3. Verify that component `inputs`/`outputs` are consistent with connections ([§13.2](#132-consistency), rules 9-10).
4. The graph may be cyclic (recurrent architectures). Do not assume acyclicity.

### D.3 Operator Type Resolution

When resolving operator types:

1. Check if `type` is in the standard registry ([§7.1](#71-standard-operator-types)).
2. If not, treat the component as an opaque node with its `params` preserved.
3. Do not fail on unknown types.
4. For `custom` type, use the `name` field as a human-readable description.

### D.4 Parameter Type Coercion

When reading parameters:

- JSON integers → `int64`
- JSON floats → `float64`
- JSON booleans → `bool`
- JSON strings → `string` (or symbolic dimension if in a shape array)
- JSON arrays → `list` of mixed `int64`/`string`
- Do not coerce between types (e.g. do not treat `768` as `768.0`).

### D.5 Round-Trip Fidelity

To ensure round-trip fidelity (read → write → read produces identical semantics):

1. Preserve all fields, including unknown ones.
2. Preserve key ordering within objects (use an ordered map, not a hash map).
3. Do not modify parameter values during transit.
4. Preserve numeric precision (do not convert integers to floats).
5. Preserve `null` values in extension fields (but `null` is not a valid parameter value).

---

## License

This specification is licensed under the Creative Commons Attribution 4.0 International License (CC-BY-4.0) and the Apache License 2.0. Implementations may choose either license.
