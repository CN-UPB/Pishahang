/**
 * Utility functions to work with Zeit's SWR hook
 */

/**
 * Given a list of objects (`objectList`) that have a unique `id` attribute, as well as a single
 * object `newObject` with an `id` attribute:
 *
 * * Appends `newObject` to `objectList` if an object with an equal `id` does not yet exists
 * * Replaces any object `x` in `objectList` which has `x.id == newObject.id` with `newObject`
 *
 * @returns The updated version of `objectList`
 */
export function updateObjectListById(
  objectList: Required<{ id: any }>[],
  newObject: Required<{ id: any }>
) {
  if (objectList == null) {
    return null;
  }

  let isReplaced = false;
  const updatedObjectList = objectList.filter((current) => {
    if (current.id === newObject.id) {
      isReplaced = true;
      return newObject;
    } else {
      return current;
    }
  });

  if (isReplaced) {
    return updatedObjectList;
  } else {
    objectList.push(newObject);
    return objectList;
  }
}
