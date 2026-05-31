part of 'widgets.dart';

/// An interactive SVG-based body atlas widget that displays anatomical elements
/// (muscles, organs, bones, skin) and supports tap and hover interactions.
///
/// This widget renders an SVG asset and provides hit-testing capabilities to
/// detect user interactions with individual anatomical elements. It supports
/// custom coloring for selected or highlighted elements and optional hover
/// effects on desktop/web platforms.
///
/// Type parameter [I] represents the specific type of anatomical element info
/// (e.g., [MuscleInfo], [OrganInfo]) that extends [AtlasElementInfo].
///
/// Example usage:
/// ```dart
/// BodyAtlasView<MuscleInfo>(
///   view: AtlasAsset.musclesFront,
///   resolver: const MuscleResolver(),
///   colorMapping: {muscle1: Colors.red, muscle2: Colors.blue},
///   hoveredOver: currentMuscle,
///   hoverColor: (color) => color.withValues(alpha: 0.5),
///   onTapElement: (muscle) => print('Tapped: ${muscle.displayName}'),
///   onHoverOverElement: (muscle) => setState(() => hovered = muscle),
/// )
/// ```
class BodyAtlasView<I extends AtlasElementInfo> extends StatefulWidget {
  /// The SVG asset containing the anatomical diagram to display.
  ///
  /// This asset should contain SVG path elements with IDs that match
  /// the element IDs in the resolver.
  final AtlasAsset view;

  /// Injected mapping from SVG id -> domain element info (muscle/organ/bone/skin).
  ///
  /// The resolver is used to convert SVG element IDs from the asset into
  /// strongly-typed element info objects of type [I].
  final AtlasResolver<I> resolver;

  /// Explicit color mapping by element info (e.g., selection/engagement).
  ///
  /// Maps specific element info objects to their desired colors. This is
  /// typically used to highlight selected or engaged elements. Colors in
  /// this mapping take precedence over hover colors.
  ///
  /// A null color value will use the original SVG color for that element.
  final Map<I, Color?>? colorMapping;

  /// Optional hover styling (desktop/web).
  ///
  /// The element info object that is currently being hovered over.
  /// When non-null and [hoverColor] is provided, this element will be
  /// rendered with the hover color styling.
  final I? hoveredOver;

  /// Function to compute hover color from the original element color.
  ///
  /// Called when an element is hovered (specified by [hoveredOver]).
  /// Receives the original color of the SVG element and should return
  /// the desired hover color, or null to keep the original color.
  ///
  /// Example: `(color) => color.withValues(alpha: 0.5)`
  final Color? Function(Color)? hoverColor;

  /// Callback invoked when a user taps on an anatomical element.
  ///
  /// The callback receives the [AtlasElementInfo] object corresponding
  /// to the tapped SVG element. This is typically used to handle element
  /// selection or navigation.
  final ValueChanged<I>? onTapElement;

  /// Callback invoked when the hover state changes (desktop/web only).
  ///
  /// The callback receives the [AtlasElementInfo] object being hovered over,
  /// or null when the hover exits. This is only active on desktop and web
  /// platforms and requires a non-null value to enable hover tracking.
  final ValueChanged<I?>? onHoverOverElement;

  const BodyAtlasView({
    super.key,
    required this.view,
    required this.resolver,
    this.colorMapping,
    this.hoveredOver,
    this.hoverColor,
    this.onTapElement,
    this.onHoverOverElement,
  });

  @override
  State<BodyAtlasView<I>> createState() => _BodyAtlasViewState<I>();
}

class _BodyAtlasViewState<I extends AtlasElementInfo> extends State<BodyAtlasView<I>> {
  final _interactionKey = GlobalKey();
  late Future<_AtlasHitTester> _hitTester;
  String? _hoveredId;

  @override
  void initState() {
    super.initState();
    _hitTester = _AtlasHitTester.load(widget.view);
  }

  @override
  void didUpdateWidget(covariant BodyAtlasView<I> oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.view != widget.view) {
      _hitTester = _AtlasHitTester.load(widget.view);
      _hoveredId = null;
    }
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData(:platform, :colorScheme) = Theme.of(context);
    final isDesktop = kIsWeb || <TargetPlatform>[.windows, .linux, .macOS].contains(platform);

    return LayoutBuilder(
      builder: (context, constraints) {
        return FutureBuilder<_AtlasHitTester>(
          future: _hitTester,
          builder: (context, snapshot) {
            final tester = snapshot.data;

            // Release-mode bug history: this used to be `SvgAsset(...)` with
            // a closure colorMapper that captured `widget`, `colorScheme`,
            // and the surrounding `_BodyAtlasViewState`. On Android release
            // (vector_graphics 2.0.34+) SVG decode crosses an isolate boundary
            // and SendPort rejects unsendable closures — atlas silently
            // failed to render on physical devices (Galaxy S25 v10-v17 log:
            // "Illegal argument in isolate message: object is unsendable").
            // Fix: concrete `ColorMapper` subclass with only Sendable fields.
            final svg = SvgPicture.asset(
              widget.view.path,
              package: AtlasAsset.package,
              fit: BoxFit.contain,
              alignment: Alignment.center,
              colorMapper: _BodyAtlasColorMapper<I>(
                resolver: widget.resolver,
                colorMapping: widget.colorMapping,
                hoveredOver: widget.hoveredOver,
                defaultHoverColor: colorScheme.secondary,
              ),
            );

            Widget interactiveChild = GestureDetector(
              behavior: .opaque,
              onTapDown: switch ((widget.onTapElement, tester)) {
                (ValueChanged<I> onTap, _AtlasHitTester tester) => (details) {
                  final box = _interactionKey.box;
                  if (box == null || !box.hasSize) return;

                  final local = box.globalToLocal(details.globalPosition);
                  final id = tester.hitTest(local, box.size);
                  if (id == null) return;

                  final info = widget.resolver.tryById(id);
                  if (info == null) return;

                  onTap(info);
                },
                _ => null,
              },
              child: svg,
            );

            if (isDesktop && tester != null && widget.onHoverOverElement != null) {
              interactiveChild = MouseRegion(
                hitTestBehavior: HitTestBehavior.opaque,
                cursor: SystemMouseCursors.click,
                onExit: (_) => _emit(null),
                onHover: (event) {
                  final box = _interactionKey.box;
                  if (box == null || !box.hasSize) return;

                  final local = box.globalToLocal(event.position);
                  final id = tester.hitTest(local, box.size);
                  _emit(id);
                },
                child: interactiveChild,
              );
            }

            return SizedBox.expand(
              key: _interactionKey,
              child: interactiveChild,
            );
          },
        );
      },
    );
  }

  void _emit(String? id) {
    if (_hoveredId == id) return;
    _hoveredId = id;

    final cb = widget.onHoverOverElement;
    if (cb == null) return;

    cb(id == null ? null : widget.resolver.tryById(id));
  }
}

extension on GlobalKey {
  RenderBox? get box => currentContext?.findRenderObject() as RenderBox?;
}

/// Isolate-safe `ColorMapper` for the body atlas. Fields are immutable
/// Sendable values (no captured closures, no widget/state references), so
/// vector_graphics' SendPort-based isolate decode can transport this object
/// without `Illegal argument in isolate message: object is unsendable`.
///
/// `hoverColor` (the per-element color-derivation closure on `BodyAtlasView`)
/// is intentionally NOT plumbed here — closures cross isolate boundaries
/// poorly. Hover falls back to the theme `colorScheme.secondary` captured at
/// build time as `defaultHoverColor`. Apps that need custom hover color
/// derivation should fork this class.
class _BodyAtlasColorMapper<I extends AtlasElementInfo> extends ColorMapper {
  const _BodyAtlasColorMapper({
    required this.resolver,
    required this.colorMapping,
    required this.hoveredOver,
    required this.defaultHoverColor,
  });

  final AtlasResolver<I> resolver;
  final Map<I, Color?>? colorMapping;
  final I? hoveredOver;
  final Color defaultHoverColor;

  @override
  Color substitute(
    String? id,
    String elementName,
    String attributeName,
    Color color,
  ) {
    if (id == null) return color;
    final info = resolver.tryById(id);
    if (info == null) return color;
    final highlighted = colorMapping?[info];
    if (highlighted != null) return highlighted;
    final hovered = hoveredOver;
    if (hovered != null && identical(info, hovered)) return defaultHoverColor;
    return color;
  }
}
